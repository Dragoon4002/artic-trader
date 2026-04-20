"""In-memory live state cache for agents. DB is source of truth."""
import threading
from typing import Any

_lock = threading.Lock()
_state: dict[str, dict[str, Any]] = {}


def update(agent_id: str, status: dict) -> None:
    with _lock:
        _state[agent_id] = status


def get(agent_id: str) -> dict | None:
    with _lock:
        return _state.get(agent_id)


def remove(agent_id: str) -> None:
    with _lock:
        _state.pop(agent_id, None)


def all_states() -> dict[str, dict]:
    with _lock:
        return dict(_state)
