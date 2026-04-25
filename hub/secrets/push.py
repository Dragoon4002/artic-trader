"""Decrypt user secrets and POST them to a freshly-woken user-server.

Called by `vm.service.wake` right before marking status=running. The user-server
exposes `/hub/secrets/refresh` behind mTLS + X-Hub-Secret. Plaintext secrets never
persist on the user-server disk — they sit in process memory only.
"""

from __future__ import annotations

import logging
import os

import httpx
from sqlalchemy import select

from ..config import settings
from ..db import base as db_base
from ..db.models.secret import UserSecret
from . import crypto

logger = logging.getLogger(__name__)


async def push(user_id: str, vm_endpoint: str) -> None:
    """Decrypt all of user's secrets and POST to user-server."""
    async with db_base.async_session() as db:
        rows = (
            (await db.execute(select(UserSecret).where(UserSecret.user_id == user_id)))
            .scalars()
            .all()
        )

    payload: dict[str, str] = {}
    for row in rows:
        try:
            payload[row.key_name] = crypto.decrypt(row.encrypted_value)
        except Exception as e:
            logger.warning("decrypt failed for %s / %s: %s", user_id, row.key_name, e)

    for env_key in ("TWELVE_DATA_API_KEY",):
        val = os.getenv(env_key, "").strip()
        if val:
            payload[env_key] = val

    if not payload:
        return

    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        # verify=False is alpha-only; real mTLS cert bundle wires in with utils/mtls.py.
        r = await client.post(
            f"{vm_endpoint.rstrip('/')}/hub/secrets/refresh",
            headers={"X-Hub-Secret": settings.INTERNAL_SECRET},
            json={"secrets": payload},
        )
    if r.status_code >= 400:
        logger.warning("secrets push non-2xx: %s %s", r.status_code, r.text)
