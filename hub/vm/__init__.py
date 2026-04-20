"""VM provisioning, wake, drain, snapshot."""

from .provider import VMHandle, VMProvider, VMProviderError
from .registry import VMRegistry, VMState, registry
from .service import VMService, WakeResult, build_default_service

_service: VMService | None = None


def get_service() -> VMService:
    """Module-level singleton so other modules (auth router, etc.) can reach
    the same VMService instance that hub.server wired into middleware.

    First call builds it; hub.server also calls this on startup to attach the
    secrets_push hook and to hydrate the registry.
    """
    global _service
    if _service is None:
        _service = build_default_service()
    return _service


__all__ = [
    "VMHandle",
    "VMProvider",
    "VMProviderError",
    "VMRegistry",
    "VMState",
    "VMService",
    "WakeResult",
    "build_default_service",
    "get_service",
    "registry",
]
