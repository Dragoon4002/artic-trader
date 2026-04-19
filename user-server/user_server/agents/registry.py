"""In-process live-state for spawned agents.

DB is source of truth for metadata (agents row). Registry tracks runtime-only
fields: container name/port for inter-container HTTP, last-seen heartbeat.
Wiped on user-server restart; wake flow rebuilds by scanning `docker ps`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LiveState:
    container_id: str
    container_name: str
    port: int = 8000
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime | None = None


_registry: dict[uuid.UUID, LiveState] = {}


def put(agent_id: uuid.UUID, state: LiveState) -> None:
    _registry[agent_id] = state


def get(agent_id: uuid.UUID) -> LiveState | None:
    return _registry.get(agent_id)


def remove(agent_id: uuid.UUID) -> LiveState | None:
    return _registry.pop(agent_id, None)


def ids() -> list[uuid.UUID]:
    return list(_registry.keys())


def touch(agent_id: uuid.UUID) -> None:
    state = _registry.get(agent_id)
    if state is not None:
        state.last_heartbeat = datetime.now(timezone.utc)


def clear() -> None:
    _registry.clear()
