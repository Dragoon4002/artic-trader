"""VM provisioning, wake, drain, snapshot."""

from .provider import VMHandle, VMProvider, VMProviderError
from .registry import VMRegistry, VMState, registry
from .service import VMService, WakeResult, build_default_service

__all__ = [
    "VMHandle",
    "VMProvider",
    "VMProviderError",
    "VMRegistry",
    "VMState",
    "VMService",
    "WakeResult",
    "build_default_service",
    "registry",
]
