"""Hub push client — reports status/trades/logs/on-chain decisions to hub."""
import os
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

HUB_URL = os.getenv("HUB_URL", "")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


class HubCallback:
    """Persistent async client for pushing data to hub internal endpoints."""

    def __init__(self, hub_url: str = "", internal_secret: str = ""):
        self._hub_url = hub_url or HUB_URL
        self._secret = internal_secret or INTERNAL_SECRET
        self._client: httpx.AsyncClient | None = None
        self._log_buffer: list[dict] = []

    @property
    def enabled(self) -> bool:
        return bool(self._hub_url)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._hub_url,
                headers={"X-Internal-Secret": self._secret},
                timeout=5.0,
            )
        return self._client

    async def report_status(self, agent_id: str, status: dict) -> None:
        if not self.enabled:
            return
        try:
            client = await self._get_client()
            await client.post(f"/internal/agents/{agent_id}/status", json=status)
        except Exception as e:
            logger.debug(f"[HubCallback] status push failed: {e}")

    async def report_trade(self, trade: dict) -> None:
        if not self.enabled:
            return
        try:
            client = await self._get_client()
            await client.post("/internal/trades", json=trade)
        except Exception as e:
            logger.warning(f"[HubCallback] trade push failed: {e}")

    async def report_onchain_trade(
        self, agent_id: str, tx_hash: str, side: str,
        entry_price: float, exit_price: float | None,
        pnl_bps: int, detail_json: str,
    ) -> None:
        if not self.enabled:
            return
        try:
            client = await self._get_client()
            await client.post("/internal/onchain-trades", json={
                "agent_id": agent_id,
                "tx_hash": tx_hash,
                "side": side,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl_bps": pnl_bps,
                "detail_json": detail_json,
            })
        except Exception as e:
            logger.warning(f"[HubCallback] onchain trade push failed: {e}")

    async def report_onchain_decision(self, agent_id: str, tx_hash: str, reasoning_text: str) -> None:
        if not self.enabled:
            return
        try:
            client = await self._get_client()
            await client.post("/internal/onchain-decisions", json={
                "agent_id": agent_id,
                "tx_hash": tx_hash,
                "reasoning_text": reasoning_text,
            })
        except Exception as e:
            logger.warning(f"[HubCallback] onchain push failed: {e}")

    def buffer_log(self, level: str, message: str) -> None:
        self._log_buffer.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        })

    async def flush_logs(self, agent_id: str) -> None:
        if not self.enabled or not self._log_buffer:
            return
        batch = self._log_buffer.copy()
        self._log_buffer.clear()
        try:
            client = await self._get_client()
            await client.post("/internal/logs", json={
                "agent_id": agent_id,
                "entries": batch,
            })
        except Exception as e:
            logger.warning(f"[HubCallback] log flush failed: {e}")
            self._log_buffer.extend(batch)  # re-buffer on failure

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Module-level singleton + backward-compat functions
_instance: HubCallback | None = None


def _get() -> HubCallback:
    global _instance
    if _instance is None:
        _instance = HubCallback()
    return _instance


async def report_status(agent_id: str, status: dict) -> None:
    await _get().report_status(agent_id, status)


async def report_trade(trade: dict) -> None:
    await _get().report_trade(trade)


async def report_onchain_trade(
    agent_id: str, tx_hash: str, side: str,
    entry_price: float, exit_price: float | None,
    pnl_bps: int, detail_json: str,
) -> None:
    await _get().report_onchain_trade(agent_id, tx_hash, side, entry_price, exit_price, pnl_bps, detail_json)


async def report_onchain_decision(agent_id: str, tx_hash: str, reasoning_text: str) -> None:
    await _get().report_onchain_decision(agent_id, tx_hash, reasoning_text)


async def flush_logs(agent_id: str, entries: list | None = None) -> None:
    """Flush buffered logs. `entries` param kept for backward compat but ignored — uses internal buffer."""
    await _get().flush_logs(agent_id)


def buffer_log(level: str, message: str) -> None:
    _get().buffer_log(level, message)
