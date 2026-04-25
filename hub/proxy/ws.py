"""WebSocket proxy for /ws/u/* — pipes frames between client and user-server.

Auth: client passes ?token=<jwt> on the URL since browser WebSocket APIs cannot
set custom headers. Hub resolves the user, wakes the VM if cold, then opens
a downstream WS to user-server's /hub/ws/agents/{id}/logs and bridges frames
in both directions.
"""
from __future__ import annotations

import asyncio
import logging

import websockets
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from ..auth import service as auth_service
from ..config import settings
from ..vm.service import WakeResult
from ..vm import get_service, registry

router = APIRouter(tags=["proxy-ws"])

_log = logging.getLogger(__name__)


async def _resolve_user(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return auth_service.verify_jwt(token)
    except Exception:
        return None


@router.websocket("/ws/u/agents/{agent_id}/status")
async def ws_agent_status(ws: WebSocket, agent_id: str, token: str = Query(default="")):
    # Status WS is not yet implemented end-to-end; close cleanly so clients fall back to polling.
    await ws.accept()
    try:
        await ws.send_json({"type": "error", "code": "NOT_IMPLEMENTED"})
    finally:
        await ws.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/ws/u/agents/{agent_id}/logs")
async def ws_agent_logs(ws: WebSocket, agent_id: str, token: str = Query(default="")):
    user_id = await _resolve_user(token)
    if not user_id:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Wake the VM if cold so the downstream WS can connect.
    state = registry.get(user_id)
    if state is None:
        await ws.accept()
        await ws.send_json({"type": "error", "code": "VM_NOT_PROVISIONED"})
        await ws.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    if state.status != "running" or not state.endpoint:
        result = await get_service().wake(user_id)
        if result != WakeResult.OK:
            await ws.accept()
            await ws.send_json({"type": "error", "code": "VM_NOT_READY"})
            await ws.close(code=status.WS_1011_INTERNAL_ERROR)
            return
        state = registry.get(user_id)
        if state is None or not state.endpoint:
            await ws.accept()
            await ws.send_json({"type": "error", "code": "VM_ENDPOINT_MISSING"})
            await ws.close(code=status.WS_1011_INTERNAL_ERROR)
            return

    base = state.endpoint.rstrip("/")
    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
    upstream_url = f"{ws_base}/hub/ws/agents/{agent_id}/logs"
    headers = {"X-Hub-Secret": settings.HUB_SECRET or settings.INTERNAL_SECRET or ""}

    await ws.accept()
    try:
        async with websockets.connect(upstream_url, additional_headers=headers) as upstream:
            async def client_to_upstream():
                try:
                    while True:
                        msg = await ws.receive_text()
                        await upstream.send(msg)
                except WebSocketDisconnect:
                    return
                except Exception:
                    return

            async def upstream_to_client():
                try:
                    async for msg in upstream:
                        if isinstance(msg, bytes):
                            await ws.send_bytes(msg)
                        else:
                            await ws.send_text(msg)
                except Exception:
                    return

            done, pending = await asyncio.wait(
                [asyncio.create_task(client_to_upstream()), asyncio.create_task(upstream_to_client())],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    except Exception as e:
        _log.warning("ws bridge error: %s", e)
        try:
            await ws.send_json({"type": "error", "code": "UPSTREAM_FAILED"})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
