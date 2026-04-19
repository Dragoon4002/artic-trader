"""LLM proxy routes: auth, rate-limit, provider dispatch, key injection.

Swaps in a fake provider to avoid any SDK import or network.
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@x:5432/x")
os.environ.setdefault("HUB_SECRET", "dev-hub")
os.environ.setdefault("INTERNAL_SECRET", "dev-internal")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from user_server.llm import providers, rate_limit, secrets_cache  # noqa: E402
from user_server.server import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    rate_limit.reset()
    secrets_cache.clear()
    yield
    rate_limit.reset()
    secrets_cache.clear()


@pytest.fixture
def fake_provider():
    seen: list[tuple] = []

    def _p(messages: list[dict], model: str, api_key: str) -> str:
        seen.append((model, api_key, len(messages)))
        return f"OK:{model}"

    providers.register("fakep", _p, key_name="FAKE_KEY")
    return seen


AGENT_H = {"X-Internal-Secret": "dev-internal", "X-Agent-Id": "a1"}


def test_llm_plan_requires_internal_secret():
    with TestClient(app) as tc:
        r = tc.post("/llm/plan", json={"symbol": "BTCUSDT", "provider": "fakep", "model": "m1"})
        assert r.status_code == 401


def test_llm_plan_missing_key_401(fake_provider):
    with TestClient(app) as tc:
        r = tc.post(
            "/llm/plan",
            json={"symbol": "BTCUSDT", "provider": "fakep", "model": "m1"},
            headers=AGENT_H,
        )
        assert r.status_code == 401
        assert "FAKE_KEY" in r.text


def test_llm_plan_roundtrip_with_cached_key(fake_provider):
    secrets_cache.put("FAKE_KEY", "sk-fake")
    with TestClient(app) as tc:
        r = tc.post(
            "/llm/plan",
            json={"symbol": "BTCUSDT", "regime": "bull", "provider": "fakep", "model": "m1"},
            headers=AGENT_H,
        )
        assert r.status_code == 200, r.text
        assert r.json()["reply"] == "OK:m1"
        assert fake_provider[0][1] == "sk-fake"


def test_rate_limit_after_60(fake_provider):
    secrets_cache.put("FAKE_KEY", "sk-fake")
    with TestClient(app) as tc:
        for _ in range(60):
            r = tc.post(
                "/llm/plan",
                json={"symbol": "BTCUSDT", "provider": "fakep", "model": "m1"},
                headers=AGENT_H,
            )
            assert r.status_code == 200
        r61 = tc.post(
            "/llm/plan",
            json={"symbol": "BTCUSDT", "provider": "fakep", "model": "m1"},
            headers=AGENT_H,
        )
        assert r61.status_code == 429


def test_unknown_provider_validation(fake_provider):
    with TestClient(app) as tc:
        r = tc.post(
            "/llm/chat",
            json={"messages": [{"role": "user", "content": "hi"}], "provider": "nope", "model": "m"},
            headers=AGENT_H,
        )
        assert r.status_code == 422
