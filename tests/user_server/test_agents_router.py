"""End-to-end test of /agents/* router against real Postgres + fake docker SDK."""
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
    os.environ["AGENT_IMAGE"] = "artic-app:dev"
    os.environ["AGENT_NETWORK"] = "artic-test"

    for mod in [m for m in list(__import__("sys").modules) if m.startswith("user_server")]:
        del __import__("sys").modules[mod]

    yield async_url

    for mod in [m for m in list(__import__("sys").modules) if m.startswith("user_server")]:
        del __import__("sys").modules[mod]
    for key in ("HUB_SECRET", "INTERNAL_SECRET", "AGENT_IMAGE", "AGENT_NETWORK", "DATABASE_URL"):
        os.environ.pop(key, None)


@pytest.fixture
def fake_docker():
    container = MagicMock()
    container.id = "sha256:deadbeef"
    container.name = "artic-agent-fake"

    client = MagicMock()
    client.containers.run.return_value = container
    client.containers.get.return_value = container
    return client, container


@pytest.fixture
def http(app_env, fake_docker):
    from user_server.agents import spawner
    from user_server.server import app

    client, _container = fake_docker
    spawner.set_client(client)

    with TestClient(app) as tc:
        yield tc, client

    spawner.set_client(None)


HUB_H = {"X-Hub-Secret": "dev-hub"}
AGENT_H = {"X-Internal-Secret": "dev-internal"}


def _body(symbol="BTCUSDT"):
    return {
        "name": "test-agent",
        "symbol": symbol,
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-6",
        "strategy_pool": ["ema_crossover"],
        "risk_params": {"amount_usdt": 100, "leverage": 5},
    }


def test_create_requires_hub_secret(http):
    tc, _ = http
    r = tc.post("/agents", json=_body())
    assert r.status_code == 401


def test_create_list_get_delete(http):
    tc, _ = http
    r = tc.post("/agents", json=_body(), headers=HUB_H)
    assert r.status_code == 200, r.text
    aid = r.json()["id"]
    assert r.json()["status"] == "stopped"

    r2 = tc.get("/agents", headers=HUB_H)
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = tc.get(f"/agents/{aid}", headers=HUB_H)
    assert r3.json()["id"] == aid

    r4 = tc.delete(f"/agents/{aid}", headers=HUB_H)
    assert r4.status_code == 204

    r5 = tc.get("/agents", headers=HUB_H)
    assert r5.json() == []


def test_start_stop_lifecycle(http):
    tc, docker_client = http
    aid = tc.post("/agents", json=_body(), headers=HUB_H).json()["id"]

    r = tc.post(f"/agents/{aid}/start", headers=HUB_H)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "alive"
    assert r.json()["container_id"] == "sha256:deadbeef"
    docker_client.containers.run.assert_called_once()

    r2 = tc.post(f"/agents/{aid}/stop", headers=HUB_H)
    assert r2.status_code == 200
    assert r2.json()["status"] == "stopped"
    assert r2.json()["container_id"] is None


def test_agent_push_status_requires_internal(http):
    tc, _ = http
    aid = tc.post("/agents", json=_body(), headers=HUB_H).json()["id"]

    r = tc.post(f"/agents/{aid}/status", json={"price": 65000.0})
    assert r.status_code == 401

    r2 = tc.post(f"/agents/{aid}/status", json={"price": 65000.0}, headers=AGENT_H)
    assert r2.status_code == 204


def test_agent_push_unknown_id(http):
    tc, _ = http
    r = tc.post(f"/agents/{uuid.uuid4()}/status", json={"price": 1.0}, headers=AGENT_H)
    assert r.status_code == 404
