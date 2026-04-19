"""Hub FastAPI server — entry point."""
import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db.base import async_session, engine as db_engine
from .auth.router import router as auth_router, api_keys_router
from .agents.router import router as agents_router, leaderboard_router
from .internal.router import router as internal_router
from .market_cache.service import router as market_router, refresh_all_tracked
from .market.router import router as market_price_router
from .market.price_feed import price_feed_loop
from .secrets.service import router as secrets_router, agent_secrets_router
from .ws.broadcaster import router as ws_router
from .ws.manager import broadcast_prices
from .agents.service import reconcile_dead_agents

_scheduler: AsyncIOScheduler | None = None
_price_feed_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler, _price_feed_task
    # Startup (schema managed by Alembic; see hub/alembic.ini)
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(refresh_all_tracked, "interval", seconds=settings.CANDLE_STALENESS_SECONDS, id="candle_refresh")
    _scheduler.add_job(
        reconcile_dead_agents, "interval", seconds=30,
        args=[async_session], id="health_reconcile",
    )
    _scheduler.start()

    # Start price feed background task
    _price_feed_task = asyncio.create_task(
        price_feed_loop(
            session_factory=async_session,
            broadcast_prices_fn=broadcast_prices,
            poll_seconds=settings.PRICE_POLL_SECONDS,
        )
    )

    yield

    # Shutdown
    if _price_feed_task:
        _price_feed_task.cancel()
        try:
            await _price_feed_task
        except asyncio.CancelledError:
            pass
    if _scheduler:
        _scheduler.shutdown(wait=False)
    await db_engine.dispose()


app = FastAPI(title="Artic Hub", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(agents_router)
app.include_router(leaderboard_router)
app.include_router(internal_router)
app.include_router(market_router)
app.include_router(market_price_router)
app.include_router(secrets_router)
app.include_router(agent_secrets_router)
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"ok": True, "service": "hub"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hub.server:app", host="0.0.0.0", port=settings.HUB_PORT, reload=True)
