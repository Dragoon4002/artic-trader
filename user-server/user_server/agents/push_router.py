"""Agent->user-server push endpoints. Guarded by X-Internal-Secret.

Agents POST here every tick/close. Bodies use the shared pydantic models so
client + server agree without a separate contract file.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFound
from shared.models.log import LogEntry as LogEntryIn
from shared.models.log import LogLevel

from ..db.base import get_session
from ..db.models import Agent, LogEntry, Trade
from ..security import internal_guard
from . import registry

router = APIRouter(prefix="", tags=["agent-push"], dependencies=[Depends(internal_guard)])


class StatusPush(BaseModel):
    price: float
    position_size_usdt: float | None = None
    unrealized_pnl_usdt: float | None = None


class TradePush(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    side: str
    entry_price: Decimal
    exit_price: Decimal | None = None
    size_usdt: Decimal
    leverage: int
    pnl_usdt: Decimal | None = None
    strategy: str
    open_at: datetime
    close_at: datetime | None = None
    close_reason: str | None = None


class LogsPush(BaseModel):
    entries: list[LogEntryIn] = Field(default_factory=list)


class SupervisorPush(BaseModel):
    agent_id: uuid.UUID
    action: str
    detail: str | None = None


@router.post("/agents/{agent_id}/status", status_code=204)
async def push_status(
    agent_id: uuid.UUID, body: StatusPush, db: AsyncSession = Depends(get_session)
) -> None:
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise NotFound(f"agent {agent_id} not found")
    registry.touch(agent_id)
    if agent.status != "alive":
        agent.status = "alive"
        await db.commit()


@router.post("/trades", status_code=201)
async def push_trade(body: TradePush, db: AsyncSession = Depends(get_session)) -> dict:
    exists = await db.get(Trade, body.id)
    if exists is None:
        db.add(
            Trade(
                id=body.id,
                agent_id=body.agent_id,
                side=body.side,
                entry_price=body.entry_price,
                exit_price=body.exit_price,
                size_usdt=body.size_usdt,
                leverage=body.leverage,
                pnl_usdt=body.pnl_usdt,
                strategy=body.strategy,
                open_at=body.open_at,
                close_at=body.close_at,
                close_reason=body.close_reason,
            )
        )
    else:
        exists.exit_price = body.exit_price
        exists.pnl_usdt = body.pnl_usdt
        exists.close_at = body.close_at
        exists.close_reason = body.close_reason
    await db.commit()
    return {"id": str(body.id)}


@router.post("/logs", status_code=201)
async def push_logs(body: LogsPush, db: AsyncSession = Depends(get_session)) -> dict:
    if not body.entries:
        return {"inserted": 0}
    rows = [
        LogEntry(
            agent_id=uuid.UUID(e.agent_id),
            level=_map_level(e.level),
            message=e.message,
            ts=e.ts if e.ts.tzinfo else e.ts.replace(tzinfo=timezone.utc),
        )
        for e in body.entries
    ]
    db.add_all(rows)
    await db.commit()
    return {"inserted": len(rows)}


@router.post("/supervisor", status_code=201)
async def push_supervisor(body: SupervisorPush, db: AsyncSession = Depends(get_session)) -> dict:
    db.add(
        LogEntry(
            agent_id=body.agent_id,
            level="supervisor",
            message=f"{body.action}: {body.detail or ''}",
        )
    )
    await db.commit()
    return {"ok": True}


def _map_level(level: LogLevel) -> str:
    # data-model stores TEXT; shared enum is {debug,info,warn,error}; persist raw string.
    return level.value if hasattr(level, "value") else str(level)
