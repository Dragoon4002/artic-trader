"""user-server FastAPI entry. Stub — real lifecycle lives in zone work."""
from __future__ import annotations

from fastapi import FastAPI

from shared.errors import register_error_handlers

app = FastAPI(title="artic-user-server")
register_error_handlers(app)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("user_server.server:app", host="0.0.0.0", port=8000)
