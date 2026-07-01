"""WebSocket connection pool and broadcast."""

import asyncio
import json
from collections import defaultdict
from typing import Protocol


class WebSocketLike(Protocol):
    async def send_text(self, data: str) -> None: ...

_subscribers: dict[str, set[WebSocketLike]] = defaultdict(set)
_lock = asyncio.Lock()

# Price feed subscribers (not agent-specific)
_price_subscribers: set[WebSocketLike] = set()
_price_lock = asyncio.Lock()


async def subscribe(agent_id: str, ws: WebSocketLike):
    async with _lock:
        _subscribers[agent_id].add(ws)


async def unsubscribe(agent_id: str, ws: WebSocketLike):
    async with _lock:
        _subscribers[agent_id].discard(ws)
        if not _subscribers[agent_id]:
            del _subscribers[agent_id]


async def broadcast(agent_id: str, msg_type: str, data):
    """Send to all subscribers of an agent."""
    async with _lock:
        subs = list(_subscribers.get(agent_id, []))
    if not subs:
        return
    payload = json.dumps({"type": msg_type, "data": data})
    results = await asyncio.gather(
        *(ws.send_text(payload) for ws in subs),
        return_exceptions=True,
    )
    dead = [ws for ws, result in zip(subs, results) if isinstance(result, Exception)]
    for ws in dead:
        await unsubscribe(agent_id, ws)


async def subscribe_prices(ws: WebSocketLike):
    async with _price_lock:
        _price_subscribers.add(ws)


async def unsubscribe_prices(ws: WebSocketLike):
    async with _price_lock:
        _price_subscribers.discard(ws)


async def broadcast_prices(price_cache: dict):
    """Broadcast price update to all price subscribers."""
    async with _price_lock:
        subs = list(_price_subscribers)
    if not subs:
        return
    payload = json.dumps({"type": "prices", "data": price_cache})
    results = await asyncio.gather(
        *(ws.send_text(payload) for ws in subs),
        return_exceptions=True,
    )
    dead = [ws for ws, result in zip(subs, results) if isinstance(result, Exception)]
    for ws in dead:
        await unsubscribe_prices(ws)
