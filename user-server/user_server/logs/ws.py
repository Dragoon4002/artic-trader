"""WebSocket log stream — polls the LogEntry table and forwards new rows.

Lives on user-server. Hub reverse-proxies WS frames at /ws/u/agents/{id}/logs.
Auth: requires X-Hub-Secret header (same guard as REST /hub/* routes).

Wire protocol: server pushes JSON frames {level, message, timestamp} as new
log rows arrive. Heartbeat ping every 25s to keep proxies alive.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from ..config import settings
from ..db.base import get_sessionmaker
from ..db.models import LogEntry

router = APIRouter(tags=["logs-ws"])

POLL_INTERVAL_SECONDS = 1.0
HEARTBEAT_SECONDS = 25.0


@router.websocket("/hub/ws/agents/{agent_id}/logs")
async def stream_logs(ws: WebSocket, agent_id: uuid.UUID) -> None:
    expected = settings.HUB_SECRET or settings.INTERNAL_SECRET or ""
    if expected:
        provided = ws.headers.get("x-hub-secret") or ws.query_params.get("hub_secret")
        if provided != expected:
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws.accept()
    sm = get_sessionmaker()
    last_ts: datetime = datetime.now(timezone.utc)
    last_heartbeat = asyncio.get_event_loop().time()
    try:
        while True:
            async with sm() as db:
                q = (
                    select(LogEntry)
                    .where(LogEntry.agent_id == agent_id, LogEntry.ts > last_ts)
                    .order_by(LogEntry.ts.asc())
                    .limit(500)
                )
                rows = (await db.execute(q)).scalars().all()
            for r in rows:
                await ws.send_text(
                    json.dumps(
                        {
                            "type": "log",
                            "level": r.level,
                            "message": r.message,
                            "timestamp": r.ts.isoformat() if r.ts else None,
                        }
                    )
                )
                last_ts = r.ts or last_ts

            now = asyncio.get_event_loop().time()
            if now - last_heartbeat > HEARTBEAT_SECONDS:
                await ws.send_text(json.dumps({"type": "ping", "ts": now}))
                last_heartbeat = now

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await ws.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
        return
