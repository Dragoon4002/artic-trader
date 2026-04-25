"""VM provider abstraction.

Only the 5 ops per docs/alpha/morph-vm.md §2. Any additional op requires a new row
in that spec before implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class VMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class VMHandle:
    """Running-instance reference returned from start/launch."""

    vm_id: str  # provider instance id
    endpoint: str  # internal URL (mTLS proxy target)
    snapshot_id: str | None = None


class VMProvider(Protocol):
    async def start(self, snapshot_id: str) -> VMHandle: ...
    async def configure_wake_on_http(self, vm_id: str) -> None: ...
    async def launch_user_server(
        self, vm_id: str, user_id: str, user_token: str
    ) -> str:
        """Returns the public endpoint URL for the user-server on this VM."""
        ...

    async def snapshot(self, vm_id: str) -> str:
        """Freeze VM state; return new snapshot id."""
        ...

    async def stop(self, vm_id: str) -> None: ...

    async def delete_snapshot(self, snapshot_id: str) -> None: ...

    async def health(self, endpoint: str) -> bool: ...

    async def get_status(self, vm_id: str) -> str | None:
        """Provider-side instance status ('ready'|'paused'|...) or None if deleted."""
        ...
