"""Shared fixtures for hub unit tests.

Uses in-memory SQLite so tests don't need Postgres. Each test gets a fresh DB via
`Base.metadata.create_all` over the hub models, then installs a FastAPI TestClient
with `get_session` overridden to use the test async session.
"""

from __future__ import annotations

import asyncio
import base64
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Set dev-friendly env vars BEFORE importing hub modules.
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt")
os.environ.setdefault("INTERNAL_SECRET", "test-internal")
os.environ.setdefault("KEK", base64.b64encode(b"0" * 32).decode())
os.environ.setdefault("MORPH_GOLDEN_SNAPSHOT_ID", "snap-test")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    from hub.db.models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncIterator[AsyncClient]:
    """Returns an httpx AsyncClient bound to the FastAPI app with DB override."""
    from hub import server as server_mod
    from hub.db import base as db_base

    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def _session_override():
        async with factory() as s:
            yield s

    # Swap out the global async_session factory + get_session dep.
    original_factory = db_base.async_session
    db_base.async_session = factory
    server_mod.app.dependency_overrides[db_base.get_session] = _session_override

    transport = ASGITransport(app=server_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    server_mod.app.dependency_overrides.clear()
    db_base.async_session = original_factory
