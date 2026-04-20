"""WebSocket proxy stub for /ws/u/* — pipes frames between client and user-server.

Full implementation lands alongside the user-server WebSocket routes. For this branch
it registers the paths so OpenAPI + system-map.md stay in sync; actual forwarding
returns 1011 until the user-server side lands.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

router = APIRouter(tags=["proxy-ws"])


@router.websocket("/ws/u/agents/{agent_id}/status")
async def ws_agent_status(ws: WebSocket, agent_id: str):
    await ws.accept()
    try:
        await ws.send_json({"type": "error", "code": "NOT_IMPLEMENTED"})
    finally:
        await ws.close(code=1011)


@router.websocket("/ws/u/agents/{agent_id}/logs")
async def ws_agent_logs(ws: WebSocket, agent_id: str):
    await ws.accept()
    try:
        await ws.send_json({"type": "error", "code": "NOT_IMPLEMENTED"})
    finally:
        await ws.close(code=1011)
