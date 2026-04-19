"""/strategies/* router — hub-guarded CRUD."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import Strategy
from ..security import hub_guard
from . import service

router = APIRouter(prefix="/strategies", tags=["strategies"], dependencies=[Depends(hub_guard)])


class InstallBody(BaseModel):
    source: str = Field(description="builtin / marketplace / authored")
    name: str
    code_blob: str | None = None
    marketplace_id: uuid.UUID | None = None


class StrategyOut(BaseModel):
    id: uuid.UUID
    source: str
    name: str
    code_hash: str | None
    marketplace_id: uuid.UUID | None
    installed_at: datetime

    @classmethod
    def from_row(cls, s: Strategy) -> "StrategyOut":
        return cls(
            id=s.id,
            source=s.source,
            name=s.name,
            code_hash=s.code_hash,
            marketplace_id=s.marketplace_id,
            installed_at=s.installed_at,
        )


@router.get("", response_model=list[StrategyOut])
async def list_strategies(db: AsyncSession = Depends(get_session)) -> list[StrategyOut]:
    return [StrategyOut.from_row(s) for s in await service.list_all(db)]


@router.post("", response_model=StrategyOut)
async def install(body: InstallBody, db: AsyncSession = Depends(get_session)) -> StrategyOut:
    s = await service.install(
        db,
        source=body.source,
        name=body.name,
        code_blob=body.code_blob,
        marketplace_id=body.marketplace_id,
    )
    await db.commit()
    await db.refresh(s)
    return StrategyOut.from_row(s)


@router.delete("/{sid}", status_code=204)
async def remove(sid: uuid.UUID, db: AsyncSession = Depends(get_session)) -> None:
    await service.remove(db, sid)
    await db.commit()
