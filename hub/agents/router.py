"""Agent CRUD + lifecycle endpoints — unified create-and-start flow."""
import logging
from collections import Counter
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from ..db.base import get_session
from ..db.models.agent import Agent
from . import registry
from ..db.models.trade import Trade
from ..db.models.log_entry import LogEntry
from ..db.models.user import User
from ..auth.deps import get_current_user
from ..secrets.service import resolve_secrets, store_agent_llm_key
from ..utils.symbols import normalize_symbol
from . import service as agent_svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ── Schemas ──────────────────────────────────────────────────────────────


class CreateAgentRequest(BaseModel):
    # Identity
    name: str = "Unnamed Agent"
    symbol: str

    # Trading config
    amount_usdt: float = Field(default=100.0, gt=0)
    leverage: int = Field(default=5, ge=1, le=125)
    risk_profile: str = "moderate"
    primary_timeframe: str = "15m"
    poll_seconds: float = Field(default=1.0, ge=0.5)
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
    tp_sl_mode: str = "fixed"
    supervisor_interval: float = Field(default=60.0, ge=30, le=300)
    live_mode: bool = False
    max_session_loss_pct: float = Field(default=0.10, ge=0.01, le=1.0)

    # LLM config
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None  # stored as AgentSecret, never in agents table

    # Behavior
    auto_start: bool = True


class AgentRestartRequest(BaseModel):
    """Optional overrides for restart — updates DB then spawns."""
    amount_usdt: Optional[float] = None
    leverage: Optional[int] = None
    live_mode: Optional[bool] = None


class AgentEditRequest(BaseModel):
    """All fields optional — only provided fields are updated."""
    name: Optional[str] = None
    amount_usdt: Optional[float] = None
    leverage: Optional[int] = None
    risk_profile: Optional[str] = None
    primary_timeframe: Optional[str] = None
    poll_seconds: Optional[float] = None
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
    tp_sl_mode: Optional[str] = None
    supervisor_interval: Optional[float] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    leaderboard_opt_in: Optional[bool] = None


# Fields requiring agent restart to take effect
RESTART_REQUIRED_FIELDS = {"leverage", "primary_timeframe", "live_mode", "llm_provider"}

# Fields that can be hot-reloaded into a running agent
HOT_RELOAD_FIELDS = {"amount_usdt", "tp_pct", "sl_pct", "tp_sl_mode",
                     "supervisor_interval", "poll_seconds", "risk_profile"}


class LeaderboardOptInRequest(BaseModel):
    opt_in: bool
    handle: Optional[str] = None


class KillAllRequest(BaseModel):
    confirm: str


# ── Helpers ──────────────────────────────────────────────────────────────


def _agent_response(agent: Agent) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "symbol": agent.symbol,
        "status": agent.status,
        "port": agent.port,
        "amount_usdt": agent.amount_usdt,
        "leverage": agent.leverage,
        "risk_profile": agent.risk_profile,
        "primary_timeframe": agent.primary_timeframe,
        "poll_seconds": agent.poll_seconds,
        "tp_pct": agent.tp_pct,
        "sl_pct": agent.sl_pct,
        "tp_sl_mode": agent.tp_sl_mode,
        "supervisor_interval": agent.supervisor_interval,
        "live_mode": agent.live_mode,
        "max_session_loss_pct": agent.max_session_loss_pct,
        "llm_provider": agent.llm_provider,
        "llm_model": agent.llm_model,
        "leaderboard_opt_in": agent.leaderboard_opt_in,
        "leaderboard_handle": agent.leaderboard_handle,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
    }


async def _get_owned_agent(db: AsyncSession, agent_id: str, user_id: str) -> Agent:
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


# ── Endpoints ────────────────────────────────────────────────────────────
# NOTE: kill-all must be before /{agent_id} routes to avoid path conflict


@router.post("/kill-all")
async def kill_all_agents(
    body: KillAllRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Stop ALL agents for authenticated user. Requires {"confirm": "KILL_ALL"}."""
    if body.confirm != "KILL_ALL":
        raise HTTPException(status_code=400, detail='Body must include {"confirm": "KILL_ALL"}')

    result = await db.execute(
        select(Agent).where(Agent.user_id == user.id, Agent.status == "alive")
    )
    agents = result.scalars().all()
    stopped = 0
    for agent in agents:
        try:
            await agent_svc.stop_agent(agent, db)
            stopped += 1
        except Exception:
            pass
    return {"stopped": stopped, "total": len(agents)}


@router.post("")
async def create_agent(
    body: CreateAgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Single unified endpoint: create agent, persist ALL config, spawn immediately."""
    symbol = normalize_symbol(body.symbol)

    agent = Agent(
        user_id=user.id,
        name=body.name,
        symbol=symbol,
        amount_usdt=body.amount_usdt,
        leverage=body.leverage,
        risk_profile=body.risk_profile,
        primary_timeframe=body.primary_timeframe,
        poll_seconds=body.poll_seconds,
        tp_pct=body.tp_pct,
        sl_pct=body.sl_pct,
        tp_sl_mode=body.tp_sl_mode,
        supervisor_interval=body.supervisor_interval,
        live_mode=body.live_mode,
        max_session_loss_pct=body.max_session_loss_pct,
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
        status="stopped",
    )
    db.add(agent)
    await db.flush()

    if body.llm_api_key:
        await store_agent_llm_key(db, agent.id, body.llm_provider, body.llm_api_key)

    await db.commit()
    await db.refresh(agent)

    if body.auto_start:
        secrets = await resolve_secrets(agent.id, user.id, db)
        try:
            await agent_svc.spawn_agent(agent, db, secrets)
        except Exception as e:
            agent.status = "error"
            await db.commit()
            await db.refresh(agent)
            resp = _agent_response(agent)
            resp["error"] = str(e)
            return resp

    return _agent_response(agent)


@router.get("")
async def list_agents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(
        select(Agent).where(Agent.user_id == user.id).order_by(Agent.created_at.desc())
    )
    return [_agent_response(a) for a in result.scalars().all()]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_owned_agent(db, agent_id, user.id)
    return _agent_response(agent)


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_owned_agent(db, agent_id, user.id)
    if agent.status == "alive":
        await agent_svc.stop_agent(agent, db)
    await db.delete(agent)
    await db.commit()
    return {"deleted": True}


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str,
    body: AgentRestartRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Restart a stopped agent using persisted config. Optional overrides update DB."""
    agent = await _get_owned_agent(db, agent_id, user.id)
    if agent.status == "alive":
        raise HTTPException(status_code=400, detail="Agent already running")

    if body:
        if body.amount_usdt is not None:
            agent.amount_usdt = body.amount_usdt
        if body.leverage is not None:
            agent.leverage = body.leverage
        if body.live_mode is not None:
            agent.live_mode = body.live_mode
        await db.commit()

    secrets = await resolve_secrets(agent.id, user.id, db)
    try:
        await agent_svc.spawn_agent(agent, db, secrets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    await db.refresh(agent)
    return _agent_response(agent)


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_owned_agent(db, agent_id, user.id)
    if agent.status != "alive":
        raise HTTPException(status_code=400, detail="Agent not running")
    await agent_svc.stop_agent(agent, db)
    return {"stopped": True}


@router.get("/{agent_id}/status")
async def agent_status(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_owned_agent(db, agent_id, user.id)
    if agent.status != "alive" or not agent.port:
        return {"status": agent.status, "running": False}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://localhost:{agent.port}/status", timeout=5)
            return r.json()
    except Exception:
        # Fallback to last-known status from in-memory registry
        cached = registry.get(agent_id)
        if cached:
            cached = dict(cached)
            cached["running"] = False
            cached["stale"] = True
            cached["error"] = "Container unreachable — showing last known state"
            return cached
        return {"status": agent.status, "running": False, "error": "Container unreachable"}


@router.get("/{agent_id}/logs")
async def agent_logs(
    agent_id: str,
    limit: int = 200,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await _get_owned_agent(db, agent_id, user.id)
    logs = await db.execute(
        select(LogEntry)
        .where(LogEntry.agent_id == agent_id)
        .order_by(LogEntry.timestamp.desc())
        .limit(limit)
    )
    entries = logs.scalars().all()
    return [
        {"level": e.level, "message": e.message, "timestamp": e.timestamp.isoformat()}
        for e in reversed(entries)
    ]


# ── Agent Edit ────────────────────────────────────────────────────────────


@router.patch("/{agent_id}")
async def edit_agent(
    agent_id: str,
    body: AgentEditRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Update agent config. Running agents: hot-reload or auto-restart as needed."""
    agent = await _get_owned_agent(db, agent_id, user.id)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided")

    for field, value in updates.items():
        setattr(agent, field, value)
    agent.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(agent)

    if agent.status == "alive":
        changed = set(updates.keys())
        needs_restart = bool(changed & RESTART_REQUIRED_FIELDS)
        can_hot_reload = changed & HOT_RELOAD_FIELDS

        if needs_restart:
            secrets = await resolve_secrets(agent.id, user.id, db)
            await agent_svc.stop_agent(agent, db)
            await agent_svc.spawn_agent(agent, db, secrets)
            await db.refresh(agent)
        elif can_hot_reload:
            await agent_svc.hot_reload_agent(agent)

    return _agent_response(agent)


# ── Leaderboard ───────────────────────────────────────────────────────────


@router.post("/{agent_id}/leaderboard")
async def set_leaderboard_opt_in(
    agent_id: str,
    body: LeaderboardOptInRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    agent = await _get_owned_agent(db, agent_id, user.id)
    agent.leaderboard_opt_in = body.opt_in
    if body.handle:
        agent.leaderboard_handle = body.handle.strip()[:30]
    await db.commit()
    return {
        "agent_id": agent_id,
        "leaderboard_opt_in": agent.leaderboard_opt_in,
        "handle": agent.leaderboard_handle,
    }


# Separate router for public leaderboard (no /api/agents prefix)
leaderboard_router = APIRouter(tags=["leaderboard"])


def _anonymize_owner(user_id) -> str:
    return f"trader_{str(user_id)[:8]}"


@leaderboard_router.get("/api/leaderboard")
async def get_leaderboard(
    limit: int = 20,
    sort_by: str = "total_pnl",
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """Public — no auth. Ranks opted-in agents by performance."""
    query = select(Agent).where(Agent.leaderboard_opt_in == True)
    if symbol:
        query = query.where(Agent.symbol == symbol.upper())
    result = await db.execute(query)
    agents = result.scalars().all()

    if not agents:
        return {"leaderboard": [], "total_agents": 0, "sort_by": sort_by}

    entries = []
    for agent in agents:
        trade_result = await db.execute(
            select(Trade).where(
                Trade.agent_id == agent.id,
                Trade.closed_at.isnot(None),
                Trade.pnl.isnot(None),
            )
        )
        trades = trade_result.scalars().all()
        if not trades:
            continue

        pnls = [float(t.pnl) for t in trades]
        wins = [p for p in pnls if p > 0]
        total_pnl = sum(pnls)
        win_rate = len(wins) / len(pnls)

        # Sharpe ratio
        import numpy as np
        arr = np.array(pnls)
        sharpe = float(np.mean(arr) / np.std(arr) * np.sqrt(len(arr))) if np.std(arr) > 0 else 0.0

        strategy_counts = Counter(t.strategy for t in trades if t.strategy)
        top_strategy = strategy_counts.most_common(1)[0][0] if strategy_counts else "unknown"

        owner = agent.leaderboard_handle or _anonymize_owner(agent.user_id)

        entries.append({
            "rank": 0,
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "symbol": agent.symbol,
            "owner": owner,
            "status": agent.status,
            "top_strategy": top_strategy,
            "total_trades": len(trades),
            "total_pnl_usdt": round(total_pnl, 2),
            "win_rate": round(win_rate, 3),
            "sharpe_ratio": round(sharpe, 3),
            "is_running": agent.status == "alive",
        })

    sort_key_map = {
        "total_pnl": lambda x: x["total_pnl_usdt"],
        "win_rate": lambda x: x["win_rate"],
        "sharpe": lambda x: x["sharpe_ratio"],
        "trade_count": lambda x: x["total_trades"],
    }
    entries.sort(key=sort_key_map.get(sort_by, sort_key_map["total_pnl"]), reverse=True)

    for i, entry in enumerate(entries[:limit]):
        entry["rank"] = i + 1

    return {
        "leaderboard": entries[:limit],
        "total_agents": len(entries),
        "sort_by": sort_by,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

