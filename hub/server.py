"""Hub FastAPI server — alpha Phase 1 entry.

Boot sequence (lifespan):
  1. Load mTLS CA (`utils.mtls.load_ca`).
  2. Hydrate VM registry from Postgres.
  3. Start APScheduler with market-candle refresh.
  4. Start price-feed background task.
Shutdown: reverse order; cleanly close forwarder httpx clients.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import api_keys_router
from .auth.router import router as auth_router
from .config import settings
from .db.base import engine as db_engine
from .internal.router import router as internal_router
from .market.price_feed import price_feed_loop
from .market.router import router as market_router
from .market.scheduler import register as register_market_jobs
from .proxy.forwarder import Forwarder
from .proxy.middleware import WakeProxyMiddleware
from .proxy.ws import router as proxy_ws_router
from .secrets import push as secrets_push
from .secrets.service import router as secrets_router
from .utils import mtls
from .utils.errors import install_error_handlers
from .vm import build_default_service
from .ws.broadcaster import router as ws_router
from .ws.manager import broadcast_prices

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_price_feed_task: asyncio.Task | None = None

# Build proxy dependencies at module scope so the middleware stack is fixed before
# startup (FastAPI locks middleware once the app starts serving).
vm_service = build_default_service()
vm_service.secrets_push = secrets_push.push
forwarder = Forwarder(verify=False)  # dev; prod uses minted VM certs via utils.mtls


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler, _price_feed_task

    mtls.load_ca()
    await vm_service.hydrate()

    _scheduler = AsyncIOScheduler()
    register_market_jobs(_scheduler)
    _scheduler.start()

    _price_feed_task = asyncio.create_task(
        price_feed_loop(
            broadcast_prices_fn=broadcast_prices,
            poll_seconds=settings.PRICE_POLL_SECONDS,
        )
    )

    try:
        yield
    finally:
        if _price_feed_task:
            _price_feed_task.cancel()
            try:
                await _price_feed_task
            except asyncio.CancelledError:
                pass
        if _scheduler:
            _scheduler.shutdown(wait=False)
        await forwarder.aclose()
        await db_engine.dispose()


app = FastAPI(title="Artic Hub", version="0.1.0-alpha", lifespan=lifespan)

install_error_handlers(app)

app.add_middleware(WakeProxyMiddleware, vm_service=vm_service, forwarder=forwarder)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(internal_router)
app.include_router(market_router)
app.include_router(secrets_router)
app.include_router(ws_router)
app.include_router(proxy_ws_router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "hub"}


@app.get("/health/ready")
async def health_ready() -> dict:
    """Shallow readiness: DB connect. VM provider + market freshness deferred to monitoring."""
    from sqlalchemy import text

    async with db_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"ok": True, "checks": {"db": "ok"}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("hub.server:app", host="0.0.0.0", port=settings.HUB_PORT, reload=True)
