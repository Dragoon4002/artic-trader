"""Hub-pull sync endpoint: GET /hub/indexer/since?ts=<iso8601>&limit=<int>."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import IndexerTx
from ..security import hub_guard

router = APIRouter(prefix="/hub/indexer", tags=["hub-indexer"], dependencies=[Depends(hub_guard)])


class IndexerRow(BaseModel):
    tx_hash: str
    user_id: str
    agent_id: str
    kind: str
    amount_usdt: str | None
    block_number: int
    tags: dict
    created_at: datetime


class SinceResponse(BaseModel):
    rows: list[IndexerRow]


@router.get("/since", response_model=SinceResponse)
async def since(
    ts: datetime = Query(..., description="ISO8601; inclusive lower bound on created_at"),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_session),
) -> SinceResponse:
    q = (
        select(IndexerTx)
        .where(IndexerTx.created_at >= ts)
        .order_by(IndexerTx.created_at.asc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return SinceResponse(
        rows=[
            IndexerRow(
                tx_hash=r.tx_hash,
                user_id=str(r.user_id),
                agent_id=str(r.agent_id),
                kind=r.kind,
                amount_usdt=str(r.amount_usdt) if r.amount_usdt is not None else None,
                block_number=r.block_number,
                tags=r.tags,
                created_at=r.created_at,
            )
            for r in rows
        ]
    )
