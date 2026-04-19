"""user-server FastAPI entry."""
from __future__ import annotations

from fastapi import FastAPI

from shared.errors import register_error_handlers

from .agents.push_router import router as agent_push_router
from .agents.router import router as agents_router
from .indexer.query import router as indexer_query_router
from .llm.router import router as llm_router
from .strategies.router import router as strategies_router

app = FastAPI(title="artic-user-server")
register_error_handlers(app)

app.include_router(agents_router)
app.include_router(agent_push_router)
app.include_router(strategies_router)
app.include_router(llm_router)
app.include_router(indexer_query_router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("user_server.server:app", host="0.0.0.0", port=8000)
