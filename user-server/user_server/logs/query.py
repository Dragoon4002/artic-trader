"""Hub-pull log query: GET /hub/logs/{agent_id}?limit=<int>"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import LogEntry
from ..security import hub_guard

router = APIRouter(prefix="/hub/logs", tags=["hub-logs"], dependencies=[Depends(hub_guard)])


class LogRow(BaseModel):
    level: str
    message: str
    timestamp: datetime


class LogsResponse(BaseModel):
    rows: list[LogRow]


@router.get("/{agent_id}", response_model=LogsResponse)
async def get_logs(
    agent_id: uuid.UUID,
    limit: int = Query(200, ge=1, le=2000),
    db: AsyncSession = Depends(get_session),
) -> LogsResponse:
    q = (
        select(LogEntry)
        .where(LogEntry.agent_id == agent_id)
        .order_by(LogEntry.ts.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return LogsResponse(
        rows=[LogRow(level=r.level, message=r.message, timestamp=r.ts) for r in reversed(rows)]
    )
