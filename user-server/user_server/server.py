"""user-server FastAPI entry. Routers wired; background jobs gated on schema."""
from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from shared.errors import register_error_handlers

from .agents.push_router import router as agent_push_router
from .agents.router import router as agents_router
from .db.base import get_sessionmaker
from .hub_callback.router import router as hub_router
from .indexer import flusher
from .indexer.query import router as indexer_query_router
from .trades.query import router as trades_query_router
from .logs.query import router as logs_query_router
from .logs.ws import router as logs_ws_router
from .llm.router import router as llm_router
from .otel import setup as otel_setup
from .strategies.router import router as strategies_router
from .utils.wait_for_schema import wait_for_schema

_scheduler: AsyncIOScheduler | None = None


async def _flush_job() -> None:
    sm = get_sessionmaker()
    async with sm() as db:
        await flusher.flush(db)


@asynccontextmanager
async def lifespan(_: FastAPI):
    otel_setup()
    try:
        await wait_for_schema(["agents", "indexer_tx"])
    except RuntimeError:
        pass  # dev: schema may come online later; don't block boot
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_flush_job, "interval", minutes=30, id="indexer_flush")
    _scheduler.start()
    try:
        yield
    finally:
        if _scheduler is not None:
            _scheduler.shutdown(wait=False)


app = FastAPI(title="artic-user-server", lifespan=lifespan)
register_error_handlers(app)

app.include_router(agents_router)
app.include_router(agent_push_router)
app.include_router(strategies_router)
app.include_router(llm_router)
app.include_router(indexer_query_router)
app.include_router(trades_query_router)
app.include_router(logs_query_router)
app.include_router(logs_ws_router)
app.include_router(hub_router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("user_server.server:app", host="0.0.0.0", port=8000)
