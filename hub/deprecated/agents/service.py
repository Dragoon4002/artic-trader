"""Agent spawn/stop logic — reads ALL config from Agent model."""
import asyncio
import logging
import os
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from ..config import settings
from ..docker import manager as docker_mgr
from ..docker.ports import acquire_port, release_port
from ..db.models.agent import Agent
from . import registry

logger = logging.getLogger(__name__)


def _get_hub_url() -> str:
    """Hub URL for agent containers to call back."""
    if os.path.exists("/.dockerenv"):
        return f"http://hub:{settings.HUB_PORT}"
    return f"http://host.docker.internal:{settings.HUB_PORT}"


def _build_start_request(agent: Agent) -> dict:
    """Build the /start payload from persisted Agent model — no external params."""
    req = {
        "symbol": agent.symbol,
        "amount_usdt": agent.amount_usdt,
        "leverage": agent.leverage,
        "poll_seconds": agent.poll_seconds,
        "risk_profile": agent.risk_profile,
        "primary_timeframe": agent.primary_timeframe,
        "live_mode": agent.live_mode,
        "tp_sl_mode": agent.tp_sl_mode,
        "supervisor_interval_seconds": agent.supervisor_interval,
    }
    if agent.tp_pct is not None:
        req["tp_pct"] = agent.tp_pct
    if agent.sl_pct is not None:
        req["sl_pct"] = agent.sl_pct
    if agent.llm_provider:
        req["llm_provider"] = agent.llm_provider
    return req


async def spawn_agent(agent: Agent, db: AsyncSession, secrets: dict) -> None:
    """Spawn Docker container, health-poll, send /start.

    All trading config is read from Agent model. Secrets dict contains
    resolved API keys (LLM, exchange, etc.) injected as env vars.
    """
    port = acquire_port()

    env_vars = {
        "HUB_URL": _get_hub_url(),
        "HUB_AGENT_ID": agent.id,
        "INTERNAL_SECRET": settings.INTERNAL_SECRET,
        "SYMBOL": agent.symbol,
        **secrets,
    }

    try:
        container_id = await asyncio.to_thread(docker_mgr.run, agent.id, port, env_vars)
    except Exception as e:
        release_port(port)
        raise RuntimeError(f"Failed to start container — is Docker running? ({e})")

    # Poll /health every 500ms for up to 20s
    base = f"http://localhost:{port}"
    healthy = False
    async with httpx.AsyncClient() as client:
        for _ in range(40):
            await asyncio.sleep(0.5)
            try:
                r = await client.get(f"{base}/health", timeout=2)
                if r.status_code == 200:
                    healthy = True
                    break
            except Exception:
                continue

    if not healthy:
        await asyncio.to_thread(docker_mgr.stop_and_remove, container_id)
        release_port(port)
        raise RuntimeError(
            f"Agent container started but didn't become healthy within 20s — "
            f"check Docker logs: docker logs artic-agent-{agent.id}"
        )

    # Send /start — built entirely from Agent model
    start_request = _build_start_request(agent)
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{base}/start", json=start_request, timeout=10)
        if r.status_code != 200:
            await asyncio.to_thread(docker_mgr.stop_and_remove, container_id)
            release_port(port)
            raise RuntimeError(f"Agent rejected start command: {r.text}")

    agent.status = "alive"
    agent.container_id = container_id
    agent.port = port
    await db.commit()


async def hot_reload_agent(agent: Agent) -> bool:
    """Push updated config to running agent via POST /config."""
    if not agent.port:
        return False
    try:
        payload = {
            "amount_usdt": agent.amount_usdt,
            "tp_pct": agent.tp_pct,
            "sl_pct": agent.sl_pct,
            "tp_sl_mode": agent.tp_sl_mode,
            "supervisor_interval_seconds": agent.supervisor_interval,
            "poll_seconds": agent.poll_seconds,
            "risk_profile": agent.risk_profile,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"http://localhost:{agent.port}/config",
                json=payload,
            )
            return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Hot reload failed for {agent.id}: {e}")
        return False


async def stop_agent(agent: Agent, db: AsyncSession) -> None:
    """Send /stop, wait, Docker stop+remove."""
    if agent.port:
        base = f"http://localhost:{agent.port}"
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{base}/stop", timeout=5)
        except Exception:
            pass
        await asyncio.sleep(3)

    if agent.container_id:
        await asyncio.to_thread(docker_mgr.stop_and_remove, agent.container_id)

    if agent.port:
        release_port(agent.port)

    agent.status = "stopped"
    agent.container_id = None
    agent.port = None
    await db.commit()


async def reconcile_dead_agents(session_factory) -> None:
    """Ping all 'alive' agents, mark unreachable ones as stopped."""
    async with session_factory() as db:
        result = await db.execute(select(Agent).where(Agent.status == "alive"))
        agents = result.scalars().all()
        if not agents:
            return

        async with httpx.AsyncClient(timeout=3) as client:
            for agent in agents:
                if not agent.port:
                    agent.status = "stopped"
                    agent.container_id = None
                    registry.remove(agent.id)
                    logger.info(f"Reconcile: {agent.id[:8]} marked stopped (no port)")
                    continue
                try:
                    r = await client.get(f"http://localhost:{agent.port}/health")
                    if r.status_code == 200:
                        continue
                except Exception:
                    pass
                # Container unreachable — clean up
                release_port(agent.port)
                registry.remove(agent.id)
                logger.info(f"Reconcile: {agent.id[:8]} marked stopped (unreachable)")
                agent.status = "stopped"
                agent.container_id = None
                agent.port = None

        await db.commit()
