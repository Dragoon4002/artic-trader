"""/hub/secrets/refresh, /hub/drain, /hub/halt."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock

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
    os.environ["HUB_URL"] = ""  # flusher returns no_hub_url

    for mod in [m for m in list(__import__("sys").modules) if m.startswith("user_server")]:
        del __import__("sys").modules[mod]

    yield async_url

    for mod in [m for m in list(__import__("sys").modules) if m.startswith("user_server")]:
        del __import__("sys").modules[mod]


HUB_H = {"X-Hub-Secret": "dev-hub"}


def test_secrets_refresh_updates_cache(app_env):
    from user_server.llm import secrets_cache
    from user_server.server import app

    with TestClient(app) as tc:
        r = tc.post(
            "/hub/secrets/refresh",
            json={"secrets": {"OPENAI_API_KEY": "sk-o", "ANTHROPIC_API_KEY": "sk-a"}},
            headers=HUB_H,
        )
        assert r.status_code == 200
        assert r.json()["loaded"] == 2
    assert secrets_cache.get("OPENAI_API_KEY") == "sk-o"
    assert secrets_cache.get("ANTHROPIC_API_KEY") == "sk-a"


def test_drain_stops_agents_and_refuses_further_starts(app_env):
    from user_server.agents import service as agents_service
    from user_server.agents import spawner
    from user_server.server import app

    container = MagicMock(id="sha256:x", name="artic-agent-x")
    client = MagicMock()
    client.containers.run.return_value = container
    client.containers.get.return_value = container
    spawner.set_client(client)

    try:
        with TestClient(app) as tc:
            r = tc.post(
                "/agents",
                json={
                    "name": "a",
                    "symbol": "BTCUSDT",
                    "llm_provider": "anthropic",
                    "llm_model": "claude-sonnet-4-6",
                    "strategy_pool": [],
                    "risk_params": {},
                },
                headers=HUB_H,
            )
            aid = r.json()["id"]
            tc.post(f"/agents/{aid}/start", headers=HUB_H)

            r = tc.post("/hub/drain", headers=HUB_H)
            assert r.status_code == 200
            assert r.json()["stopped"] >= 1
            assert r.json()["accepting_starts"] is False

            r2 = tc.post(f"/agents/{aid}/start", headers=HUB_H)
            assert r2.status_code == 422
    finally:
        spawner.set_client(None)
        agents_service.set_accepting_starts(True)


def test_halt_idempotent(app_env):
    from user_server.agents import service as agents_service
    from user_server.server import app

    with TestClient(app) as tc:
        r = tc.post("/hub/halt", headers=HUB_H)
        assert r.status_code == 200
        r2 = tc.post("/hub/halt", headers=HUB_H)
        assert r2.status_code == 200
    agents_service.set_accepting_starts(True)
