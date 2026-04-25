from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import Trade
from ..security import hub_guard

router = APIRouter(prefix="/hub/trades", tags=["hub-trades"], dependencies=[Depends(hub_guard)])


class TradeRow(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    side: str
    entry_price: float
    exit_price: float | None
    size_usdt: float
    leverage: int
    pnl: float | None
    strategy: str
    close_reason: str | None
    opened_at: datetime
    closed_at: datetime | None
    tx_hash: str | None = None


class TradesResponse(BaseModel):
    rows: list[TradeRow]


@router.get("/{agent_id}", response_model=TradesResponse)
async def get_trades(
    agent_id: uuid.UUID,
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_session),
) -> TradesResponse:
    q = (
        select(Trade)
        .where(Trade.agent_id == agent_id)
        .order_by(Trade.open_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return TradesResponse(
        rows=[
            TradeRow(
                id=r.id,
                agent_id=r.agent_id,
                side=r.side,
                entry_price=float(r.entry_price),
                exit_price=float(r.exit_price) if r.exit_price is not None else None,
                size_usdt=float(r.size_usdt),
                leverage=r.leverage,
                pnl=float(r.pnl_usdt) if r.pnl_usdt is not None else None,
                strategy=r.strategy,
                close_reason=r.close_reason,
                opened_at=r.open_at,
                closed_at=r.close_at,
                tx_hash=r.tx_hash,
            )
            for r in rows
        ]
    )
