"""Internal endpoints: agent -> hub push (status, trades, logs, on-chain decisions)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.base import get_session
from ..db.models.trade import Trade
from ..db.models.log_entry import LogEntry
from ..db.models.onchain import OnchainDecision, OnchainTrade
from ..agents import registry
from ..ws.manager import broadcast

router = APIRouter(prefix="/internal", tags=["internal"])


def _check_secret(request: Request):
    secret = request.headers.get("X-Internal-Secret", "")
    if secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Invalid internal secret")


class StatusPush(BaseModel):
    running: bool = False
    symbol: str | None = None
    last_price: float | None = None
    side: str = "FLAT"
    entry_price: float | None = None
    position_size_usdt: float | None = None
    leverage: int | None = None
    unrealized_pnl_usdt: float | None = None
    last_action: str | None = None
    last_reason: str | None = None
    active_strategy: str | None = None


class TradePush(BaseModel):
    agent_id: str
    side: str
    entry_price: float
    exit_price: float | None = None
    size_usdt: float | None = None
    leverage: int | None = None
    pnl: float | None = None
    strategy: str | None = None
    close_reason: str | None = None
    tx_hash: str | None = None


class OnchainPush(BaseModel):
    agent_id: str
    tx_hash: str
    reasoning_text: str


class OnchainTradePush(BaseModel):
    agent_id: str
    tx_hash: str
    side: str
    entry_price: float
    exit_price: float | None = None
    pnl_bps: int = 0
    detail_json: str = ""


class LogPush(BaseModel):
    agent_id: str
    entries: list[dict]


@router.post("/agents/{agent_id}/status")
async def push_status(agent_id: str, body: StatusPush, request: Request):
    _check_secret(request)
    data = body.model_dump()
    registry.update(agent_id, data)
    await broadcast(agent_id, "status", data)
    return {"ok": True}


@router.post("/trades")
async def push_trade(
    body: TradePush,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    _check_secret(request)
    trade = Trade(
        agent_id=body.agent_id,
        side=body.side,
        entry_price=body.entry_price,
        exit_price=body.exit_price,
        size_usdt=body.size_usdt,
        leverage=body.leverage,
        pnl=body.pnl,
        strategy=body.strategy,
        close_reason=body.close_reason,
        tx_hash=body.tx_hash,
    )
    db.add(trade)
    await db.commit()
    return {"ok": True}


@router.post("/onchain-decisions")
async def push_onchain_decision(
    body: OnchainPush,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    _check_secret(request)
    decision = OnchainDecision(
        agent_id=body.agent_id,
        session_id=b"",  # populated by on-chain logger when available
        tx_hash=body.tx_hash,
        block_number=0,  # populated when block is confirmed
        reasoning_text=body.reasoning_text,
    )
    db.add(decision)
    await db.commit()
    return {"ok": True}


@router.post("/onchain-trades")
async def push_onchain_trade(
    body: OnchainTradePush,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    _check_secret(request)
    record = OnchainTrade(
        agent_id=body.agent_id,
        tx_hash=body.tx_hash,
        side=body.side,
        entry_price=body.entry_price,
        exit_price=body.exit_price,
        pnl_bps=body.pnl_bps,
        detail_json=body.detail_json,
    )
    db.add(record)
    await db.commit()
    return {"ok": True}


@router.post("/logs")
async def push_logs(
    body: LogPush,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    _check_secret(request)
    for entry in body.entries:
        log = LogEntry(
            agent_id=body.agent_id,
            level=entry.get("level", "info"),
            message=entry.get("message", ""),
        )
        db.add(log)
    await db.commit()
    await broadcast(body.agent_id, "logs", body.entries)
    return {"ok": True, "count": len(body.entries)}
