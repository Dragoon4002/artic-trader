"""Agent lifecycle: persist to DB, orchestrate spawner + registry.

Separates concerns:
  * DB row mutations via the provided AsyncSession.
  * Docker via spawner.*.
  * In-memory runtime state via registry.*.

Drain-mode (A7) flips `_accepting_starts` to False; start_agent raises then.
"""
from __future__ import annotations

import asyncio
import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFound, Validation

from ..config import settings
from ..db.models import Agent
from ..llm import secrets_cache
from . import registry, spawner

_log = logging.getLogger(__name__)

_accepting_starts = True


def set_accepting_starts(value: bool) -> None:
    global _accepting_starts
    _accepting_starts = value


def accepting_starts() -> bool:
    return _accepting_starts


async def create(
    db: AsyncSession,
    *,
    name: str,
    symbol: str,
    llm_provider: str,
    llm_model: str,
    strategy_pool: list,
    risk_params: dict,
) -> Agent:
    agent = Agent(
        name=name,
        symbol=symbol,
        llm_provider=llm_provider,
        llm_model=llm_model,
        strategy_pool=strategy_pool,
        risk_params=risk_params,
    )
    db.add(agent)
    await db.flush()
    return agent


async def list_all(db: AsyncSession) -> list[Agent]:
    rows = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return list(rows.scalars())


async def get(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise NotFound(f"agent {agent_id} not found")
    return agent


async def delete(db: AsyncSession, agent_id: uuid.UUID) -> None:
    agent = await get(db, agent_id)
    if agent.status in ("starting", "alive"):
        raise Validation("cannot delete a running agent; stop it first")
    await db.delete(agent)


async def start(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    if not _accepting_starts:
        raise Validation("user-server is draining; starts are refused")
    agent = await get(db, agent_id)
    if agent.status == "alive":
        return agent
    agent.status = "starting"
    await db.flush()
    import os
    gemini_key = secrets_cache.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    twelve_key = secrets_cache.get("TWELVE_DATA_API_KEY") or os.getenv("TWELVE_DATA_API_KEY")
    owner_init = secrets_cache.get("OWNER_INIT_NAME") or os.getenv("OWNER_INIT_NAME")
    env = spawner.build_env(
        agent,
        internal_secret=settings.INTERNAL_SECRET,
        user_server_url=settings.USER_SERVER_INTERNAL_URL,
        llm_api_key=gemini_key,
        twelve_data_api_key=twelve_key,
        owner_init_name=owner_init,
    )
    container = await asyncio.to_thread(spawner.spawn, agent.id, env)
    registry.put(agent.id, registry.LiveState(container_id=container.id, container_name=container.name))
    agent.container_id = container.id
    agent.port = 8000

    agent_base = f"http://{spawner.container_name(agent.id)}:8000"
    try:
        agent_base = await _wait_healthy(agent_base, container)
    except Validation:
        # DEBUG: keep container alive for inspection on health failure
        _log.warning("health failed; leaving container %s alive for inspection", container.name)
        registry.remove(agent.id)
        raise

    rp = agent.risk_params or {}
    payload = {
        "symbol": agent.symbol,
        "amount_usdt": rp.get("amount_usdt", 100),
        "leverage": rp.get("leverage", 1),
        "poll_seconds": rp.get("poll_seconds", 5),
        "tp_pct": rp.get("tp_pct"),
        "sl_pct": rp.get("sl_pct"),
        "risk_profile": rp.get("risk_profile", "moderate"),
        "primary_timeframe": rp.get("primary_timeframe", "15m"),
        "live_mode": False,
        "tp_sl_mode": rp.get("tp_sl_mode", "fixed"),
        "supervisor_interval_seconds": rp.get("supervisor_interval", 60),
        "llm_provider": agent.llm_provider,
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{agent_base}/start", json=payload, timeout=10.0)
            if resp.status_code >= 300:
                _log.warning("POST /start returned %s", resp.status_code)
        except Exception as exc:
            _log.warning("POST /start failed: %s", exc)

    agent.status = "alive"
    return agent


async def _wait_healthy(agent_base: str, container: object) -> str:
    deadline = 15.0
    interval = 0.5
    elapsed = 0.0
    url = f"{agent_base}/health"
    fallback_tried = False

    async with httpx.AsyncClient() as client:
        while elapsed < deadline:
            try:
                resp = await client.get(url, timeout=2.0)
                if resp.status_code == 200:
                    return agent_base
            except (httpx.ConnectError, httpx.TimeoutException):
                if not fallback_tried:
                    try:
                        await asyncio.to_thread(container.reload)  # type: ignore[union-attr]
                        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})  # type: ignore[union-attr]
                        for net_info in networks.values():
                            ip = net_info.get("IPAddress")
                            if ip:
                                agent_base = f"http://{ip}:8000"
                                url = f"{agent_base}/health"
                                fallback_tried = True
                                break
                    except Exception:
                        pass
            await asyncio.sleep(interval)
            elapsed += interval

    raise Validation("agent container failed to become healthy")


async def stop(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    agent = await get(db, agent_id)
    if agent.status in ("stopped", "stopping"):
        return agent
    agent.status = "stopping"
    await db.flush()
    state = registry.get(agent_id)
    cid = state.container_id if state else agent.container_id
    if cid:
        await asyncio.to_thread(spawner.stop, cid)
    registry.remove(agent_id)
    agent.status = "stopped"
    agent.container_id = None
    agent.port = None
    return agent


async def start_all(db: AsyncSession) -> list[Agent]:
    agents = await list_all(db)
    out: list[Agent] = []
    for a in agents:
        if a.status != "alive":
            out.append(await start(db, a.id))
        else:
            out.append(a)
    return out


async def stop_all(db: AsyncSession) -> list[Agent]:
    agents = await list_all(db)
    out: list[Agent] = []
    for a in agents:
        out.append(await stop(db, a.id))
    return out


