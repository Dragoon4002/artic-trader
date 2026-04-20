"""VMService wake flow with a fake provider."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from hub.db import base as db_base
from hub.db.models import User, UserVM
from hub.vm import VMHandle, VMRegistry, VMService, WakeResult

pytestmark = pytest.mark.asyncio


class FakeProvider:
    """Minimal VMProvider-conformant fake. Configurable health + timings."""

    def __init__(self, *, healthy_after: int = 0, fail_start: bool = False):
        self.calls: list[tuple[str, tuple]] = []
        self._healthy_after = healthy_after
        self._probes = 0
        self._fail_start = fail_start

    async def start(self, snapshot_id: str) -> VMHandle:
        self.calls.append(("start", (snapshot_id,)))
        if self._fail_start:
            from hub.vm import VMProviderError

            raise VMProviderError("boom")
        return VMHandle(
            vm_id="vm-1", endpoint="http://fake-vm", snapshot_id=snapshot_id
        )

    async def configure_wake_on_http(self, vm_id: str) -> None:
        self.calls.append(("wake_on", (vm_id,)))

    async def launch_user_server(
        self, vm_id: str, user_id: str, user_token: str
    ) -> str:
        self.calls.append(("launch", (vm_id, user_id)))
        return "http://fake-vm"

    async def snapshot(self, vm_id: str) -> str:
        self.calls.append(("snapshot", (vm_id,)))
        return "snap-new"

    async def stop(self, vm_id: str) -> None:
        self.calls.append(("stop", (vm_id,)))

    async def delete_snapshot(self, snapshot_id: str) -> None:
        self.calls.append(("del_snap", (snapshot_id,)))

    async def health(self, endpoint: str) -> bool:
        self._probes += 1
        return self._probes > self._healthy_after


@pytest.fixture
async def vm_setup(db_engine, monkeypatch):
    """Point global async_session at the test engine + return a pristine VMService."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr(db_base, "async_session", factory)

    # Seed one user + VM row.
    async with factory() as s:
        user = User(email="v@b.com", password_hash="x")
        s.add(user)
        await s.commit()
        await s.refresh(user)
        s.add(UserVM(user_id=user.id, status="stopped"))
        await s.commit()

    fake = FakeProvider(healthy_after=1)
    svc = VMService(provider=fake, registry=VMRegistry())
    await svc.hydrate()
    return svc, fake, user.id


async def test_wake_marks_running_and_pushes_secrets(vm_setup, monkeypatch):
    svc, fake, uid = vm_setup
    pushed = []

    async def _push(user_id, endpoint):
        pushed.append((user_id, endpoint))

    svc.secrets_push = _push
    monkeypatch.setenv("MORPH_GOLDEN_SNAPSHOT_ID", "snap-test")

    result = await svc.wake(uid)
    assert result == WakeResult.RUNNING
    assert any(name == "launch" for name, _ in fake.calls)
    assert pushed == [(uid, "http://fake-vm")]
    assert svc.registry.get(uid).status == "running"


async def test_wake_returns_pending_on_health_timeout(db_engine, monkeypatch):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr(db_base, "async_session", factory)
    # Seed user + VM.
    async with factory() as s:
        user = User(email="t@b.com", password_hash="x")
        s.add(user)
        await s.commit()
        await s.refresh(user)
        s.add(UserVM(user_id=user.id, status="stopped"))
        await s.commit()

    # Never-healthy provider; wake timeout forced to 0.2s.
    from hub.config import settings as hub_settings

    monkeypatch.setattr(hub_settings, "VM_WAKE_TIMEOUT_SECONDS", 0.2)
    never = FakeProvider(healthy_after=9999)
    svc = VMService(provider=never, registry=VMRegistry())
    await svc.hydrate()

    result = await svc.wake(user.id)
    assert result == WakeResult.PENDING
    assert svc.registry.get(user.id).status == "waking"


async def test_wake_failed_when_provider_raises(db_engine, monkeypatch):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr(db_base, "async_session", factory)
    async with factory() as s:
        user = User(email="f@b.com", password_hash="x")
        s.add(user)
        await s.commit()
        await s.refresh(user)
        s.add(UserVM(user_id=user.id, status="stopped"))
        await s.commit()

    broken = FakeProvider(fail_start=True)
    svc = VMService(provider=broken, registry=VMRegistry())
    await svc.hydrate()

    result = await svc.wake(user.id)
    assert result == WakeResult.FAILED
    assert svc.registry.get(user.id).status == "error"
