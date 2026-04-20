"""WebSocket endpoints for streaming agent status, logs, and prices."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .manager import subscribe, subscribe_prices, unsubscribe, unsubscribe_prices

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/agents/{agent_id}/status")
async def ws_agent_status(ws: WebSocket, agent_id: str):
    await ws.accept()
    await subscribe(agent_id, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; client can send pings
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe(agent_id, ws)


@router.websocket("/ws/agents/{agent_id}/logs")
async def ws_agent_logs(ws: WebSocket, agent_id: str):
    await ws.accept()
    await subscribe(agent_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe(agent_id, ws)


@router.websocket("/ws/prices")
async def ws_prices(ws: WebSocket):
    """Stream live price updates. No auth required — agents connect from containers."""
    await ws.accept()
    await subscribe_prices(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe_prices(ws)
