"""CRUD for `strategies` rows. Sources: builtin / marketplace / authored."""
from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFound, Validation

from ..db.models import Strategy
from .builtins import BUILTINS

VALID_SOURCES = ("builtin", "marketplace", "authored")


async def list_all(db: AsyncSession) -> list[Strategy]:
    rows = await db.execute(select(Strategy).order_by(Strategy.installed_at.desc()))
    return list(rows.scalars())


async def get(db: AsyncSession, sid: uuid.UUID) -> Strategy:
    s = await db.get(Strategy, sid)
    if s is None:
        raise NotFound(f"strategy {sid} not found")
    return s


async def install(
    db: AsyncSession,
    *,
    source: str,
    name: str,
    code_blob: str | None = None,
    marketplace_id: uuid.UUID | None = None,
) -> Strategy:
    if source not in VALID_SOURCES:
        raise Validation(f"invalid source {source!r}; one of {VALID_SOURCES}")
    if source == "builtin" and name not in BUILTINS:
        raise Validation(f"unknown builtin {name!r}")
    if source in ("authored", "marketplace") and not code_blob:
        raise Validation("code_blob required for authored/marketplace strategies")
    code_hash = hashlib.sha256(code_blob.encode()).hexdigest() if code_blob else None
    s = Strategy(
        source=source,
        name=name,
        code_hash=code_hash,
        code_blob=code_blob,
        marketplace_id=marketplace_id,
    )
    db.add(s)
    await db.flush()
    return s


async def remove(db: AsyncSession, sid: uuid.UUID) -> None:
    s = await get(db, sid)
    await db.delete(s)
