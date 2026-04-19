"""Gate background tasks until required tables exist.

Per tasks/lessons.md: `make dev` boots the app before `make migrate` runs.
Fires all startup jobs against an empty schema otherwise. Each background
task should `await wait_for_schema([...])` before first DB query.

If DATABASE_URL points to an unreachable host, we bail fast (RuntimeError)
so callers — typically the FastAPI lifespan — can degrade gracefully. The
table-existence poll only runs once the engine can actually connect.
"""
from __future__ import annotations

import asyncio
from typing import Iterable

from sqlalchemy import text

from ..db.base import get_engine


async def wait_for_schema(tables: Iterable[str], *, timeout_s: float = 60.0, interval_s: float = 0.5) -> None:
    try:
        engine = get_engine()
    except RuntimeError as exc:
        raise RuntimeError(f"engine unavailable: {exc}") from exc

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — unreachable host, auth fail, etc.
        raise RuntimeError(f"database unreachable: {type(exc).__name__}") from exc

    deadline = asyncio.get_event_loop().time() + timeout_s
    missing = list(tables)
    while missing and asyncio.get_event_loop().time() < deadline:
        still_missing: list[str] = []
        async with engine.connect() as conn:
            for t in missing:
                try:
                    await conn.execute(text(f"SELECT 1 FROM {t} LIMIT 0"))
                except Exception:  # noqa: BLE001
                    still_missing.append(t)
        missing = still_missing
        if missing:
            await asyncio.sleep(interval_s)
    if missing:
        raise RuntimeError(f"schema did not stabilize; missing {missing}")
