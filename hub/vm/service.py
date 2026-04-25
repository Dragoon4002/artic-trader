"""VM lifecycle orchestration — provision, wake, drain, stop, snapshot.

State machine: stopped → waking → running → draining → stopped.
`wake(user_id)` blocks up to `VM_WAKE_TIMEOUT_SECONDS` waiting for health; on timeout
it returns WAKE_PENDING so the proxy layer can return 202 to the client.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import base as db_base
from ..db.models.user_vm import UserVM
from .provider import VMHandle, VMProvider, VMProviderError
from .registry import VMRegistry, VMState
from .registry import registry as _default_registry

logger = logging.getLogger(__name__)


class WakeResult(str, Enum):
    RUNNING = "running"
    PENDING = "pending"
    FAILED = "failed"


SecretsPushFn = Callable[[str, str], Awaitable[None]]  # (user_id, vm_endpoint) -> None


class VMService:
    """High-level VM operations. Holds a provider and optional secrets-push hook."""

    def __init__(
        self,
        provider: VMProvider,
        registry: VMRegistry = _default_registry,
        secrets_push: SecretsPushFn | None = None,
    ):
        self.provider = provider
        self.registry = registry
        self.secrets_push = secrets_push
        self._wake_locks: dict[str, asyncio.Lock] = {}

    # ------------------------ hydration ------------------------

    async def hydrate(self) -> None:
        """Populate registry from Postgres on startup."""
        async with db_base.async_session() as db:
            rows = (await db.execute(select(UserVM))).scalars().all()
            for row in rows:
                self.registry.put(
                    VMState(
                        user_id=row.user_id,
                        provider_vm_id=row.provider_vm_id,
                        endpoint=row.endpoint,
                        status=row.status,
                        last_active_at=row.last_active_at,
                    )
                )

    # ------------------------ ops ------------------------

    async def provision_for_user(self, db: AsyncSession, user_id: str) -> UserVM:
        """Called on user signup. Creates a user_vms row in status=stopped.

        Does NOT start the VM — first client request triggers wake-proxy.
        """
        existing = (
            await db.execute(select(UserVM).where(UserVM.user_id == user_id))
        ).scalar_one_or_none()
        if existing:
            return existing
        row = UserVM(user_id=user_id, status="stopped", image_tag=settings.VM_IMAGE_TAG)
        db.add(row)
        await db.commit()
        await db.refresh(row)
        self.registry.put(
            VMState(
                user_id=user_id,
                provider_vm_id=None,
                endpoint=None,
                status="stopped",
                last_active_at=None,
            )
        )
        return row

    async def wake(self, user_id: str) -> WakeResult:
        """Cold-wake a stopped VM. Idempotent — concurrent callers share one wake."""
        lock = self._wake_locks.setdefault(user_id, asyncio.Lock())
        async with lock:
            state = self.registry.get(user_id)
            if state is None:
                # Not provisioned — caller should 404.
                return WakeResult.FAILED
            if state.status == "running" and state.endpoint:
                return WakeResult.RUNNING

            self.registry.set_status(user_id, "waking")
            await self._persist_status(user_id, "waking")

            try:
                handle = await self._start_or_resume(user_id, state)
            except VMProviderError as e:
                logger.exception("wake failed for user %s: %s", user_id, e)
                # Best-effort: if _start_or_resume persisted a vm_id before
                # failing (e.g. launch_user_server died after start), stop it
                # so we don't leak a paused Morph instance.
                current = self.registry.get(user_id)
                leaked = current.provider_vm_id if current else None
                if leaked:
                    try:
                        await self.provider.stop(leaked)
                    except Exception as ce:
                        logger.warning("cleanup stop of %s failed: %s", leaked, ce)
                    await self._clear_vm_mapping(user_id)
                self.registry.set_status(user_id, "error")
                await self._persist_status(user_id, "error")
                return WakeResult.FAILED

            # Poll health up to VM_WAKE_TIMEOUT_SECONDS.
            deadline = (
                asyncio.get_event_loop().time() + settings.VM_WAKE_TIMEOUT_SECONDS
            )
            while asyncio.get_event_loop().time() < deadline:
                if await self.provider.health(handle.endpoint):
                    break
                await asyncio.sleep(0.5)
            else:
                # Keep status=waking; client retries.
                return WakeResult.PENDING

            # Push secrets before marking running (per runtime-flow.md §1).
            if self.secrets_push:
                try:
                    await self.secrets_push(user_id, handle.endpoint)
                except Exception as e:
                    logger.warning("secrets push failed for %s: %s", user_id, e)

            now = datetime.now(timezone.utc)
            self.registry.set_status(
                user_id,
                "running",
                provider_vm_id=handle.vm_id,
                endpoint=handle.endpoint,
                last_active_at=now,
            )
            await self._persist_running(user_id, handle.vm_id, handle.endpoint, now)
            return WakeResult.RUNNING

    async def touch(self, user_id: str) -> None:
        """Update last_active_at on successful proxy hit."""
        now = datetime.now(timezone.utc)
        self.registry.set_status(user_id, "running", last_active_at=now)
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            if row:
                row.last_active_at = now
                await db.commit()

    async def drain(self, user_id: str) -> bool:
        """Snapshot + stop a running VM. Returns True on full success."""
        state = self.registry.get(user_id)
        if state is None or state.provider_vm_id is None:
            return False
        self.registry.set_status(user_id, "draining")
        await self._persist_status(user_id, "draining")
        try:
            new_snapshot = await self.provider.snapshot(state.provider_vm_id)
            await self.provider.stop(state.provider_vm_id)
            async with db_base.async_session() as db:
                row = (
                    await db.execute(select(UserVM).where(UserVM.user_id == user_id))
                ).scalar_one_or_none()
                if row:
                    row.status = "stopped"
                    row.snapshot_id = new_snapshot
                    row.endpoint = None
                    row.provider_vm_id = None
                    await db.commit()
            self.registry.set_status(
                user_id,
                "stopped",
                provider_vm_id=None,
                endpoint=None,
            )
            return True
        except VMProviderError as e:
            logger.exception("drain failed for %s: %s", user_id, e)
            self.registry.set_status(user_id, "error")
            await self._persist_status(user_id, "error")
            return False

    # ------------------------ internals ------------------------

    async def _start_or_resume(self, user_id: str, state: VMState):
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            existing_vm_id = row.provider_vm_id if row else None
            existing_endpoint = row.endpoint if row else None
            snapshot_id = (
                row.snapshot_id if row else None
            ) or settings.MORPH_GOLDEN_SNAPSHOT_ID
            user_token = settings.INTERNAL_SECRET

        # Case A/B: existing mapping with endpoint — reuse. wake()'s outer
        # health poll hits the endpoint; Morph auto-resumes a paused instance
        # on first HTTP.
        if existing_vm_id and existing_endpoint:
            provider_status = await self.provider.get_status(existing_vm_id)
            if provider_status in ("ready", "paused"):
                return VMHandle(
                    vm_id=existing_vm_id,
                    endpoint=existing_endpoint,
                    snapshot_id=snapshot_id,
                )
            logger.info(
                "stale vm %s for user %s (provider status=%s); clearing mapping",
                existing_vm_id,
                user_id,
                provider_status,
            )
            await self._clear_vm_mapping(user_id)
        # Case C: vm_id persisted but no endpoint — failed mid-wake orphan.
        elif existing_vm_id:
            logger.info(
                "orphan vm %s for user %s (no endpoint); stopping before restart",
                existing_vm_id,
                user_id,
            )
            try:
                await self.provider.stop(existing_vm_id)
            except VMProviderError as e:
                logger.warning("stop of orphan %s failed: %s", existing_vm_id, e)
            await self._clear_vm_mapping(user_id)

        if not snapshot_id:
            raise VMProviderError(
                "no snapshot id (set MORPH_GOLDEN_SNAPSHOT_ID or per-user)"
            )

        # Case D: fresh start. Persist vm_id BEFORE launch_user_server so a
        # mid-wake failure leaves enough state for cleanup.
        handle = await self.provider.start(snapshot_id)
        await self._persist_vm_id(user_id, handle.vm_id)
        await self.provider.configure_wake_on_http(handle.vm_id)
        endpoint = await self.provider.launch_user_server(
            handle.vm_id, user_id, user_token
        )
        await self._persist_endpoint(user_id, endpoint)
        return VMHandle(
            vm_id=handle.vm_id, endpoint=endpoint, snapshot_id=snapshot_id
        )

    async def _persist_status(self, user_id: str, status: str) -> None:
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            if row:
                row.status = status
                await db.commit()

    async def _persist_vm_id(self, user_id: str, vm_id: str) -> None:
        self.registry.set_status(user_id, "waking", provider_vm_id=vm_id)
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            if row:
                row.provider_vm_id = vm_id
                await db.commit()

    async def _persist_endpoint(self, user_id: str, endpoint: str) -> None:
        self.registry.set_status(user_id, "waking", endpoint=endpoint)
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            if row:
                row.endpoint = endpoint
                await db.commit()

    async def _clear_vm_mapping(self, user_id: str) -> None:
        self.registry.set_status(user_id, "waking", provider_vm_id=None, endpoint=None)
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            if row:
                row.provider_vm_id = None
                row.endpoint = None
                await db.commit()

    async def _persist_running(
        self, user_id: str, vm_id: str, endpoint: str, last_active_at: datetime
    ) -> None:
        async with db_base.async_session() as db:
            row = (
                await db.execute(select(UserVM).where(UserVM.user_id == user_id))
            ).scalar_one_or_none()
            if row:
                row.status = "running"
                row.provider_vm_id = vm_id
                row.endpoint = endpoint
                row.last_active_at = last_active_at
                await db.commit()


def build_default_service() -> VMService:
    """Factory for the global VMService instance per VM_PROVIDER env."""
    from .morph_provider import MorphProvider

    if settings.VM_PROVIDER == "morph":
        return VMService(provider=MorphProvider())
    raise RuntimeError(f"unsupported VM_PROVIDER: {settings.VM_PROVIDER}")
