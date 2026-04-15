"""Adapter wrapping HubClient for TUI — single-call create+start via hub."""
import os
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from hub.client import HubClient


@dataclass
class AgentInfo:
    """Populated entirely from hub API response — no local defaults needed."""
    agent_id: str
    name: str
    symbol: str
    port: int | None = None
    alive: bool = False
    amount_usdt: float = 100.0
    leverage: int = 5
    risk_profile: str = "moderate"
    tp_pct: float | None = None
    sl_pct: float | None = None
    tp_sl_mode: str = "fixed"
    poll_seconds: float = 1.0
    live_mode: bool = False
    timeframe: str = "15m"
    supervisor_interval: float = 60.0
    llm_provider: str | None = None
    leaderboard_opt_in: bool = False
    leaderboard_handle: str | None = None


def _agent_info_from_response(data: dict) -> AgentInfo:
    """Build AgentInfo from hub's full AgentResponse dict."""
    return AgentInfo(
        agent_id=data["id"],
        name=data.get("name", "?"),
        symbol=data.get("symbol", "?"),
        port=data.get("port"),
        alive=data.get("status") == "alive",
        amount_usdt=data.get("amount_usdt", 100.0),
        leverage=data.get("leverage", 5),
        risk_profile=data.get("risk_profile", "moderate"),
        tp_pct=data.get("tp_pct"),
        sl_pct=data.get("sl_pct"),
        tp_sl_mode=data.get("tp_sl_mode", "fixed"),
        poll_seconds=data.get("poll_seconds", 1.0),
        live_mode=data.get("live_mode", False),
        timeframe=data.get("primary_timeframe", "15m"),
        supervisor_interval=data.get("supervisor_interval", 60.0),
        llm_provider=data.get("llm_provider"),
        leaderboard_opt_in=data.get("leaderboard_opt_in", False),
        leaderboard_handle=data.get("leaderboard_handle"),
    )


class HubAdapter:
    """All state from hub API. No local config caching."""

    def __init__(self, hub_url: str = "http://localhost:8000"):
        self.hub = HubClient(base_url=hub_url)
        self.agents: dict[str, AgentInfo] = {}
        self._logged_in = False

    async def login(self, email: str, password: str) -> str:
        token = await self.hub.login(email, password)
        self._logged_in = True
        return token

    async def register(self, email: str, password: str) -> str:
        token = await self.hub.register(email, password)
        self._logged_in = True
        return token

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    async def refresh_agents(self) -> None:
        """Fetch agent list from hub, rebuild self.agents from full response."""
        data = await self.hub.list_agents()
        self.agents = {a["id"]: _agent_info_from_response(a) for a in data}

    async def check_alive(self) -> None:
        await self.refresh_agents()

    async def launch(self, **kwargs) -> AgentInfo:
        """Single hub call — creates + persists + spawns. No 2-step workaround."""
        result = await self.hub.create_agent(
            symbol=kwargs.get("symbol", "BTCUSDT"),
            name=kwargs.get("name", "Unnamed Agent"),
            amount_usdt=kwargs.get("amount_usdt", 100.0),
            leverage=kwargs.get("leverage", 5),
            risk_profile=kwargs.get("risk_profile", "moderate"),
            primary_timeframe=kwargs.get("timeframe", "15m"),
            poll_seconds=kwargs.get("poll_seconds", 1.0),
            tp_pct=kwargs.get("tp_pct"),
            sl_pct=kwargs.get("sl_pct"),
            tp_sl_mode=kwargs.get("tp_sl_mode", "fixed"),
            supervisor_interval=kwargs.get("supervisor_interval", 60.0),
            live_mode=kwargs.get("live_mode", False),
            llm_provider=kwargs.get("llm_provider"),
            llm_api_key=kwargs.get("llm_api_key"),
            auto_start=True,
        )
        info = _agent_info_from_response(result)
        self.agents[info.agent_id] = info
        if result.get("error"):
            raise RuntimeError(f"Agent created but spawn failed: {result['error']}")
        return info

    async def start_agent(self, agent_id: str) -> None:
        """Restart using persisted config — no params needed."""
        await self.hub.start_agent(agent_id)
        if agent_id in self.agents:
            self.agents[agent_id].alive = True

    async def stop(self, agent_id: str) -> None:
        await self.hub.stop_agent(agent_id)
        if agent_id in self.agents:
            self.agents[agent_id].alive = False

    async def stop_all(self) -> None:
        import asyncio
        running = [aid for aid, info in self.agents.items() if info.alive]
        await asyncio.gather(*(self.stop(aid) for aid in running), return_exceptions=True)

    async def delete(self, agent_id: str) -> None:
        await self.hub.delete_agent(agent_id)
        self.agents.pop(agent_id, None)

    async def status_all(self) -> dict:
        import asyncio
        results = {}
        alive = [aid for aid, info in self.agents.items() if info.alive]

        async def _get(aid):
            try:
                return aid, await self.hub.get_status(aid)
            except Exception:
                return aid, None

        pairs = await asyncio.gather(*(_get(aid) for aid in alive), return_exceptions=True)
        for pair in pairs:
            if isinstance(pair, tuple):
                results[pair[0]] = pair[1]
        return results

    async def edit_agent(self, agent_id: str, **kwargs) -> dict:
        result = await self.hub.edit_agent(agent_id, **kwargs)
        info = _agent_info_from_response(result)
        self.agents[info.agent_id] = info
        return result

    async def set_leaderboard_opt_in(self, agent_id: str, opt_in: bool, handle: str | None = None) -> dict:
        return await self.hub.set_leaderboard_opt_in(agent_id, opt_in, handle)

    async def get_leaderboard(self, limit: int = 20, sort_by: str = "total_pnl", symbol: str | None = None) -> dict:
        return await self.hub.get_leaderboard(limit=limit, sort_by=sort_by, symbol=symbol)

    async def logs(self, agent_id: str) -> dict:
        try:
            entries = await self.hub.get_logs(agent_id)
            return {"logs": [{"level": e.get("level"), "message": e.get("message"), "ts": e.get("timestamp")} for e in entries]}
        except Exception:
            return {"logs": []}
