from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import Decision
from ..security import hub_guard

router = APIRouter(prefix="/hub/decisions", tags=["hub-decisions"], dependencies=[Depends(hub_guard)])


class DecisionRow(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    action: str
    strategy: str | None
    reasoning: str | None
    tx_hash: str | None
    reasoning_cid: str | None
    created_at: datetime


class DecisionsResponse(BaseModel):
    rows: list[DecisionRow]


@router.get("/{agent_id}", response_model=DecisionsResponse)
async def get_decisions(
    agent_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
) -> DecisionsResponse:
    q = (
        select(Decision)
        .where(Decision.agent_id == agent_id)
        .order_by(Decision.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return DecisionsResponse(
        rows=[
            DecisionRow(
                id=r.id,
                agent_id=r.agent_id,
                action=r.action,
                strategy=r.strategy,
                reasoning=r.reasoning,
                tx_hash=r.tx_hash,
                reasoning_cid=r.reasoning_cid,
                created_at=r.created_at,
            )
            for r in rows
        ]
    )
