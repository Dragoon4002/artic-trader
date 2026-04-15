"""Atomic thread-safe port allocation."""
import socket
import threading

_lock = threading.Lock()
_in_use: set[int] = set()
_START_PORT = 8010
_MAX_PORT = 8200


def _port_is_free(port: int) -> bool:
    """Check if port is actually free at the OS level."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def acquire_port() -> int:
    """Thread-safe: find first free port starting at 8010."""
    with _lock:
        for port in range(_START_PORT, _MAX_PORT):
            if port not in _in_use and _port_is_free(port):
                _in_use.add(port)
                return port
    raise RuntimeError("No free ports in range 8010-8200 — check for stale containers: docker ps")


def release_port(port: int) -> None:
    """Return port to pool."""
    with _lock:
        _in_use.discard(port)
