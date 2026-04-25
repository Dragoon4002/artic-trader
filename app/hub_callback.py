"""Push client — reports status/trades/logs to user-server from agent containers."""
import os
import uuid
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

HUB_URL = os.getenv("HUB_URL", "")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")

# App-internal log levels → standard levels stored in DB
_LEVEL_MAP: dict[str, str] = {
    "init": "info", "llm": "info", "start": "info", "tick": "debug",
    "action": "info", "sl_tp": "info", "stop": "info",
    "error": "error", "warn": "warn", "supervisor": "info",
}


class HubCallback:
    """Persistent async client for pushing data to user-server endpoints."""

    def __init__(self, hub_url: str = "", internal_secret: str = ""):
        self._hub_url = hub_url or HUB_URL
        self._secret = internal_secret or INTERNAL_SECRET
        self._client: httpx.AsyncClient | None = None
        self._log_buffer: list[dict] = []
        # trade_id tracking: agent_id → (trade_uuid, open_at)
        self._open_trades: dict[str, tuple[uuid.UUID, datetime]] = {}
        # most-recent trade_id per agent for async tx-hash patching
        self._last_trade_id: dict[str, uuid.UUID] = {}

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
            # user-server StatusPush expects: price, position_size_usdt, unrealized_pnl_usdt, active_strategy
            payload = {
                "price": status.get("last_price") or 0.0,
                "position_size_usdt": status.get("position_size_usdt"),
                "unrealized_pnl_usdt": status.get("unrealized_pnl_usdt"),
                "active_strategy": status.get("active_strategy"),
            }
            await client.post(f"/agents/{agent_id}/status", json=payload)
        except Exception as e:
            logger.debug(f"[HubCallback] status push failed: {e}")

    async def report_trade(self, trade: dict) -> None:
        if not self.enabled:
            return
        try:
            agent_id = trade.get("agent_id", "")
            has_exit = trade.get("exit_price") is not None

            if not has_exit:
                trade_id = uuid.uuid4()
                open_at = datetime.now(timezone.utc)
                self._open_trades[agent_id] = (trade_id, open_at)
            else:
                entry = self._open_trades.pop(agent_id, None)
                trade_id = entry[0] if entry else uuid.uuid4()
                open_at = entry[1] if entry else datetime.now(timezone.utc)
            self._last_trade_id[agent_id] = trade_id

            payload = {
                "id": str(trade_id),
                "agent_id": agent_id,
                "side": trade.get("side", ""),
                "entry_price": str(trade.get("entry_price", 0)),
                "exit_price": str(trade["exit_price"]) if has_exit else None,
                "size_usdt": str(trade.get("size_usdt", 0)),
                "leverage": trade.get("leverage", 1),
                "pnl_usdt": str(trade["pnl"]) if trade.get("pnl") is not None else None,
                "strategy": trade.get("strategy") or "unknown",
                "open_at": open_at.isoformat(),
                "close_at": datetime.now(timezone.utc).isoformat() if has_exit else None,
                "close_reason": trade.get("close_reason"),
                "tx_hash": trade.get("tx_hash"),
            }
            client = await self._get_client()
            await client.post("/trades", json=payload)
        except Exception as e:
            logger.warning(f"[HubCallback] trade push failed: {e}")

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
        # inject agent_id into each entry to match shared.models.log.LogEntry
        entries = [{**e, "agent_id": agent_id} for e in batch]
        try:
            client = await self._get_client()
            await client.post("/logs", json={"entries": entries})
        except Exception as e:
            logger.warning(f"[HubCallback] log flush failed: {e}")
            self._log_buffer.extend(batch)

    async def patch_trade_tx_hash(self, agent_id: str, tx_hash: str) -> None:
        """Backfill the tx_hash on the most-recent trade for `agent_id`."""
        if not self.enabled or not tx_hash:
            return
        trade_id = self._last_trade_id.get(agent_id)
        if trade_id is None:
            return
        try:
            client = await self._get_client()
            await client.post(f"/trades/{trade_id}/tx-hash", json={"tx_hash": tx_hash})
        except Exception as e:
            logger.debug(f"[HubCallback] tx_hash patch failed: {e}")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Module-level singleton
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
    if not tx_hash:
        return
    buffer_log("action", f"onchain trade tx={tx_hash} side={side} pnl_bps={pnl_bps}")
    await _get().patch_trade_tx_hash(agent_id, tx_hash)


async def report_onchain_decision(agent_id: str, tx_hash: str, reasoning_text: str) -> None:
    if not tx_hash:
        return
    buffer_log("supervisor", f"onchain decision tx={tx_hash}")


async def flush_logs(agent_id: str, entries: list | None = None) -> None:
    await _get().flush_logs(agent_id)


def buffer_log(level: str, message: str) -> None:
    _get().buffer_log(level, message)
