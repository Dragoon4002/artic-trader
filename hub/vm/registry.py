"""In-memory cache of user_vms status. Rehydrated from Postgres on startup."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True)
class VMState:
    user_id: str
    provider_vm_id: str | None
    endpoint: str | None
    status: str  # stopped | waking | running | draining | error
    last_active_at: datetime | None


class VMRegistry:
    """Thread-safe-ish (single-process asyncio) registry of VM states."""

    def __init__(self) -> None:
        self._by_user: dict[str, VMState] = {}

    def get(self, user_id: str) -> VMState | None:
        return self._by_user.get(user_id)

    def put(self, state: VMState) -> None:
        self._by_user[state.user_id] = state

    def set_status(self, user_id: str, status: str, **overrides) -> VMState | None:
        current = self._by_user.get(user_id)
        if current is None:
            return None
        new = replace(current, status=status, **overrides)
        self._by_user[user_id] = new
        return new

    def drop(self, user_id: str) -> None:
        self._by_user.pop(user_id, None)

    def snapshot(self) -> dict[str, VMState]:
        return dict(self._by_user)


registry = VMRegistry()
