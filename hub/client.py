"""Hub SDK — Python client for all Artic clients (TUI, CLI, Telegram)."""
import httpx
from typing import AsyncIterator, Optional


class HubError(Exception):
    """Human-readable hub API error. Extracts detail from JSON response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _raise_for_status(r: httpx.Response) -> None:
    """Like raise_for_status() but raises HubError with the detail message."""
    if r.is_success:
        return
    # extract detail from FastAPI's {"detail": "..."} response
    detail = None
    try:
        body = r.json()
        detail = body.get("detail") if isinstance(body, dict) else None
    except Exception:
        pass
    if not detail:
        detail = r.text or f"HTTP {r.status_code}"
    raise HubError(r.status_code, detail)


class HubClient:
    """Async client for the Artic hub API."""

    def __init__(self, base_url: str = "http://localhost:8000", token: str | None = None, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._api_key = api_key

    def _headers(self) -> dict:
        h: dict[str, str] = {}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        elif self._api_key:
            h["X-API-Key"] = self._api_key
        return h

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, headers=self._headers(), timeout=30)

    # ── Auth ─────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> str:
        async with self._client() as c:
            r = await c.post("/auth/login", json={"email": email, "password": password})
            _raise_for_status(r)
            self._token = r.json()["access_token"]
            return self._token

    async def register(self, email: str, password: str) -> str:
        async with self._client() as c:
            r = await c.post("/auth/register", json={"email": email, "password": password})
            _raise_for_status(r)
            self._token = r.json()["access_token"]
            return self._token

    # ── Agents ───────────────────────────────────────────────────────────

    async def create_agent(
        self,
        symbol: str,
        name: str = "Unnamed Agent",
        amount_usdt: float = 100.0,
        leverage: int = 5,
        risk_profile: str = "moderate",
        primary_timeframe: str = "15m",
        poll_seconds: float = 1.0,
        tp_pct: Optional[float] = None,
        sl_pct: Optional[float] = None,
        tp_sl_mode: str = "fixed",
        supervisor_interval: float = 60.0,
        live_mode: bool = False,
        max_session_loss_pct: float = 0.10,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        auto_start: bool = True,
    ) -> dict:
        """Single call: creates + persists all config + spawns agent."""
        payload = {
            "symbol": symbol,
            "name": name,
            "amount_usdt": amount_usdt,
            "leverage": leverage,
            "risk_profile": risk_profile,
            "primary_timeframe": primary_timeframe,
            "poll_seconds": poll_seconds,
            "tp_sl_mode": tp_sl_mode,
            "supervisor_interval": supervisor_interval,
            "live_mode": live_mode,
            "max_session_loss_pct": max_session_loss_pct,
            "auto_start": auto_start,
        }
        if tp_pct is not None:
            payload["tp_pct"] = tp_pct
        if sl_pct is not None:
            payload["sl_pct"] = sl_pct
        if llm_provider is not None:
            payload["llm_provider"] = llm_provider
        if llm_model is not None:
            payload["llm_model"] = llm_model
        if llm_api_key is not None:
            payload["llm_api_key"] = llm_api_key

        async with self._client() as c:
            r = await c.post("/api/agents", json=payload)
            _raise_for_status(r)
            return r.json()

    # Alias — create already auto-starts
    launch = create_agent

    async def list_agents(self) -> list:
        async with self._client() as c:
            r = await c.get("/api/agents")
            _raise_for_status(r)
            return r.json()

    async def get_agent(self, agent_id: str) -> dict:
        async with self._client() as c:
            r = await c.get(f"/api/agents/{agent_id}")
            _raise_for_status(r)
            return r.json()

    async def start_agent(self, agent_id: str, **overrides) -> dict:
        """Restart a stopped agent. No params required — uses persisted config."""
        async with self._client() as c:
            r = await c.post(
                f"/api/agents/{agent_id}/start",
                json=overrides if overrides else None,
            )
            _raise_for_status(r)
            return r.json()

    async def stop_agent(self, agent_id: str) -> dict:
        async with self._client() as c:
            r = await c.post(f"/api/agents/{agent_id}/stop")
            _raise_for_status(r)
            return r.json()

    async def delete_agent(self, agent_id: str) -> dict:
        async with self._client() as c:
            r = await c.delete(f"/api/agents/{agent_id}")
            _raise_for_status(r)
            return r.json()

    async def kill_all(self) -> dict:
        async with self._client() as c:
            r = await c.post("/api/agents/kill-all", json={"confirm": "KILL_ALL"})
            _raise_for_status(r)
            return r.json()

    async def get_status(self, agent_id: str) -> dict:
        async with self._client() as c:
            r = await c.get(f"/api/agents/{agent_id}/status")
            _raise_for_status(r)
            return r.json()

    async def get_logs(self, agent_id: str, limit: int = 200) -> list:
        async with self._client() as c:
            r = await c.get(f"/api/agents/{agent_id}/logs", params={"limit": limit})
            _raise_for_status(r)
            return r.json()

    async def edit_agent(self, agent_id: str, **kwargs) -> dict:
        """PATCH agent config. Only pass fields to change."""
        async with self._client() as c:
            r = await c.patch(
                f"/api/agents/{agent_id}",
                json={k: v for k, v in kwargs.items() if v is not None},
            )
            _raise_for_status(r)
            return r.json()

    # ── Leaderboard ──────────────────────────────────────────────────────

    async def get_leaderboard(
        self, limit: int = 20, sort_by: str = "total_pnl", symbol: Optional[str] = None,
    ) -> dict:
        """Public — no auth required."""
        params: dict = {"limit": limit, "sort_by": sort_by}
        if symbol:
            params["symbol"] = symbol.upper()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as c:
            r = await c.get("/api/leaderboard", params=params)
            _raise_for_status(r)
            return r.json()

    async def set_leaderboard_opt_in(
        self, agent_id: str, opt_in: bool, handle: Optional[str] = None,
    ) -> dict:
        payload: dict = {"opt_in": opt_in}
        if handle:
            payload["handle"] = handle
        async with self._client() as c:
            r = await c.post(f"/api/agents/{agent_id}/leaderboard", json=payload)
            _raise_for_status(r)
            return r.json()

    # ── WebSocket streaming ──────────────────────────────────────────────

    async def ws_status(self, agent_id: str) -> AsyncIterator[dict]:
        import websockets
        import json
        url = self.base_url.replace("http", "ws") + f"/ws/agents/{agent_id}/status"
        async with websockets.connect(url) as ws:
            async for msg in ws:
                yield json.loads(msg)

    async def ws_logs(self, agent_id: str) -> AsyncIterator[dict]:
        import websockets
        import json
        url = self.base_url.replace("http", "ws") + f"/ws/agents/{agent_id}/logs"
        async with websockets.connect(url) as ws:
            async for msg in ws:
                yield json.loads(msg)
