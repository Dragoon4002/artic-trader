"""`.init` username reverse lookup.

Best-effort only — a name-service outage must never block auth. Returns None
on any error. Callers persist the result to `users.init_username` +
`users.init_username_resolved_at`; refresh when the cached row is >24h old.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(hours=24)


def is_stale(resolved_at: datetime | None) -> bool:
    if resolved_at is None:
        return True
    return datetime.now(timezone.utc) - resolved_at > CACHE_TTL


async def resolve_init_name(address: str) -> str | None:
    """Reverse-lookup an address to its primary `.init` name; None if none."""
    base_url = (settings.INITIA_NAME_SERVICE_URL or "").strip()
    if not base_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{base_url.rstrip('/')}/reverse/{address}")
            if resp.status_code != 200:
                return None
            data = resp.json() or {}
            name = data.get("name") or data.get("primary_name")
            if isinstance(name, str) and name.endswith(".init"):
                return name
            return None
    except Exception as exc:
        logger.info("init name lookup failed for %s: %s", address, exc)
        return None
