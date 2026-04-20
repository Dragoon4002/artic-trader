"""Agent lifecycle: persist to DB, orchestrate spawner + registry.

Separates concerns:
  * DB row mutations via the provided AsyncSession.
  * Docker via spawner.*.
  * In-memory runtime state via registry.*.

Drain-mode (A7) flips `_accepting_starts` to False; start_agent raises then.
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFound, Validation

from ..config import settings
from ..db.models import Agent
from . import registry, spawner

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
    env = spawner.build_env(agent, internal_secret=settings.INTERNAL_SECRET, user_server_url=_self_url())
    container = await asyncio.to_thread(spawner.spawn, agent.id, env)
    registry.put(agent.id, registry.LiveState(container_id=container.id, container_name=container.name))
    agent.container_id = container.id
    agent.port = 8000
    agent.status = "alive"
    return agent


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


def _self_url() -> str:
    """URL agents use to reach user-server (resolvable on AGENT_NETWORK)."""
    return f"http://user-server:8000"
