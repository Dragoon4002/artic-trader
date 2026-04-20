"""Hub-initiated control-plane endpoints under /hub/*. All hub-guarded.

- /hub/secrets/refresh : hub pushes decrypted user secrets + WALLET_KEK
- /hub/drain           : graceful stop-all + flush, prep for snapshot
- /hub/halt            : immediate stop-all (credits depleted)

Idempotent. Return small JSON ack.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents import service as agents_service
from ..db.base import get_session
from ..indexer import flusher
from ..llm import secrets_cache
from ..security import hub_guard

router = APIRouter(prefix="/hub", tags=["hub-callback"], dependencies=[Depends(hub_guard)])


class SecretsRefreshBody(BaseModel):
    secrets: dict[str, str] = Field(default_factory=dict, description="key_name -> plaintext")


@router.post("/secrets/refresh")
async def refresh_secrets(body: SecretsRefreshBody) -> dict:
    secrets_cache.clear()
    secrets_cache.put_many(body.secrets)
    return {"loaded": len(body.secrets), "keys": secrets_cache.known_keys()}


@router.post("/drain")
async def drain(db: AsyncSession = Depends(get_session)) -> dict:
    agents_service.set_accepting_starts(False)
    stopped = await agents_service.stop_all(db)
    await db.commit()
    flush_result = await flusher.flush(db)
    return {
        "stopped": len(stopped),
        "flush": flush_result,
        "accepting_starts": agents_service.accepting_starts(),
    }


@router.post("/halt")
async def halt(db: AsyncSession = Depends(get_session)) -> dict:
    agents_service.set_accepting_starts(False)
    stopped = await agents_service.stop_all(db)
    await db.commit()
    return {"stopped": len(stopped), "accepting_starts": agents_service.accepting_starts()}
