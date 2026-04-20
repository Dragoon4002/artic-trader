"""Indexer: writer + /hub/indexer/since + flusher (fake poster)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "user-server" / "alembic.ini"


@pytest.fixture
def app_env(require_pg: str):
    sync_url = require_pg
    async_url = sync_url.replace("+psycopg2", "+asyncpg")

    eng = sa.create_engine(sync_url)
    with eng.begin() as c:
        c.execute(sa.text("DROP SCHEMA public CASCADE"))
        c.execute(sa.text("CREATE SCHEMA public"))
    eng.dispose()

    os.environ["DATABASE_URL"] = sync_url
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "user-server" / "alembic"))
    command.upgrade(cfg, "head")

    os.environ["DATABASE_URL"] = async_url
    os.environ["HUB_SECRET"] = "dev-hub"
    os.environ["INTERNAL_SECRET"] = "dev-internal"
    os.environ["HUB_URL"] = "http://fake-hub"
    os.environ["USER_ID"] = str(uuid.uuid4())
    os.environ["USER_TOKEN"] = "dev-token"

    for mod in [m for m in list(__import__("sys").modules) if m.startswith("user_server")]:
        del __import__("sys").modules[mod]

    yield async_url

    for mod in [m for m in list(__import__("sys").modules) if m.startswith("user_server")]:
        del __import__("sys").modules[mod]


async def _seed_rows(async_url: str, rows: list[dict]) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    eng = create_async_engine(async_url)
    async with eng.begin() as c:
        for r in rows:
            await c.execute(
                sa.text(
                    "INSERT INTO indexer_tx (tx_hash,user_id,agent_id,kind,amount_usdt,block_number,tags,created_at)"
                    " VALUES (:tx,:u,:a,:k,:amt,:bn,CAST(:tags AS JSONB),:ts)"
                ),
                {**r, "tags": '{"chain":"testnet"}'},
            )
    await eng.dispose()


HUB_H = {"X-Hub-Secret": "dev-hub"}


def test_since_returns_rows_after_ts(app_env):
    from user_server.server import app

    uid = uuid.uuid4()
    aid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    rows = [
        {"tx": "0xaa", "u": uid, "a": aid, "k": "trades", "amt": 100.0, "bn": 1, "ts": now - timedelta(minutes=10)},
        {"tx": "0xbb", "u": uid, "a": aid, "k": "trades", "amt": 200.0, "bn": 2, "ts": now},
    ]

    import asyncio

    asyncio.get_event_loop().run_until_complete(_seed_rows(app_env, rows))

    with TestClient(app) as tc:
        r = tc.get(
            "/hub/indexer/since",
            params={"ts": (now - timedelta(minutes=5)).isoformat()},
            headers=HUB_H,
        )
        assert r.status_code == 200, r.text
        data = r.json()["rows"]
        assert len(data) == 1
        assert data[0]["tx_hash"] == "0xbb"


@pytest.mark.asyncio
async def test_flush_posts_rows(app_env):
    from user_server.db.base import get_sessionmaker
    from user_server.indexer import flusher, writer

    uid = uuid.uuid4()
    aid = uuid.uuid4()
    sm = get_sessionmaker()
    async with sm() as db:
        await writer.write(
            db,
            tx_hash="0x01",
            user_id=uid,
            agent_id=aid,
            kind="trades",
            block_number=1,
            tags={"symbol": "BTCUSDT"},
            amount_usdt=Decimal("100.0"),
        )
        await db.commit()

    posted: list[tuple[str, dict]] = []

    class _Resp:
        def __init__(self, status: int) -> None:
            self.status_code = status

    async def fake_post(url: str, payload: dict):
        posted.append((url, payload))
        return _Resp(200)

    async with sm() as db:
        result = await flusher.flush(db, poster=fake_post)

    assert result == {"pushed": 1, "skipped": 0, "status": "ok"}
    assert posted[0][0] == "http://fake-hub/internal/v1/indexer/flush"
    assert posted[0][1]["rows"][0]["tx_hash"] == "0x01"


@pytest.mark.asyncio
async def test_flush_swallows_404(app_env):
    from user_server.db.base import get_sessionmaker
    from user_server.indexer import flusher, writer

    sm = get_sessionmaker()
    async with sm() as db:
        await writer.write(
            db,
            tx_hash="0x02",
            user_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            kind="supervise",
            block_number=2,
            tags={},
        )
        await db.commit()

    class _Resp:
        status_code = 404

    async def fake_post(url: str, payload: dict):
        return _Resp()

    async with sm() as db:
        result = await flusher.flush(db, poster=fake_post)

    assert result["status"] == "hub_endpoint_missing"
    assert result["skipped"] == 1
