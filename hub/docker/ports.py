"""Atomic thread-safe port allocation."""
import threading

_lock = threading.Lock()
_in_use: set[int] = set()
_START_PORT = 8010
_MAX_PORT = 8200


def acquire_port() -> int:
    """Thread-safe: find first free port starting at 8010."""
    with _lock:
        for port in range(_START_PORT, _MAX_PORT):
            if port not in _in_use:
                _in_use.add(port)
                return port
    raise RuntimeError("No free ports available")


def release_port(port: int) -> None:
    """Return port to pool."""
    with _lock:
        _in_use.discard(port)
