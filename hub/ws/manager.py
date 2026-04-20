"""WebSocket connection pool and broadcast."""

import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket

_subscribers: dict[str, set[WebSocket]] = defaultdict(set)
_lock = asyncio.Lock()

# Price feed subscribers (not agent-specific)
_price_subscribers: set[WebSocket] = set()
_price_lock = asyncio.Lock()


async def subscribe(agent_id: str, ws: WebSocket):
    async with _lock:
        _subscribers[agent_id].add(ws)


async def unsubscribe(agent_id: str, ws: WebSocket):
    async with _lock:
        _subscribers[agent_id].discard(ws)
        if not _subscribers[agent_id]:
            del _subscribers[agent_id]


async def broadcast(agent_id: str, msg_type: str, data):
    """Send to all subscribers of an agent."""
    async with _lock:
        subs = list(_subscribers.get(agent_id, []))
    payload = json.dumps({"type": msg_type, "data": data})
    dead = []
    for ws in subs:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await unsubscribe(agent_id, ws)


async def subscribe_prices(ws: WebSocket):
    async with _price_lock:
        _price_subscribers.add(ws)


async def unsubscribe_prices(ws: WebSocket):
    async with _price_lock:
        _price_subscribers.discard(ws)


async def broadcast_prices(price_cache: dict):
    """Broadcast price update to all price subscribers."""
    async with _price_lock:
        subs = list(_price_subscribers)
    if not subs:
        return
    payload = json.dumps({"type": "prices", "data": price_cache})
    dead = []
    for ws in subs:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await unsubscribe_prices(ws)
