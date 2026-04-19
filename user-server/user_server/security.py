"""Header-guard dependencies for hub->user-server and agent->user-server auth.

Dev: both guards compare against fixed env values. Prod: hub rotates secrets
on each VM wake via POST /hub/secrets/refresh (see hub_callback/secrets.py in A7).
"""
from __future__ import annotations

from fastapi import Header

from shared.errors import AuthInvalid, AuthRequired

from .config import settings


async def hub_guard(x_hub_secret: str | None = Header(default=None, alias="X-Hub-Secret")) -> None:
    if not settings.HUB_SECRET:
        raise AuthInvalid("HUB_SECRET not configured on user-server")
    if x_hub_secret is None:
        raise AuthRequired("X-Hub-Secret header required")
    if x_hub_secret != settings.HUB_SECRET:
        raise AuthInvalid("X-Hub-Secret mismatch")


async def internal_guard(
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret"),
) -> None:
    if not settings.INTERNAL_SECRET:
        raise AuthInvalid("INTERNAL_SECRET not configured on user-server")
    if x_internal_secret is None:
        raise AuthRequired("X-Internal-Secret header required")
    if x_internal_secret != settings.INTERNAL_SECRET:
        raise AuthInvalid("X-Internal-Secret mismatch")
