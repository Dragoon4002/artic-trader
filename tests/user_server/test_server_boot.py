"""Server boot: /health returns 200 and OpenAPI is served."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@x:5432/x")
os.environ.setdefault("HUB_SECRET", "dev-hub")
os.environ.setdefault("INTERNAL_SECRET", "dev-internal")

from fastapi.testclient import TestClient  # noqa: E402

from user_server.server import app  # noqa: E402


def test_health():
    with TestClient(app) as tc:
        r = tc.get("/health")
        assert r.status_code == 200
        assert r.json() == {"ok": True}


def test_openapi_contains_all_routers():
    with TestClient(app) as tc:
        spec = tc.get("/openapi.json").json()
    paths = set(spec["paths"].keys())
    # one representative endpoint per router
    assert "/agents" in paths
    assert "/strategies" in paths
    assert "/llm/plan" in paths
    assert "/hub/drain" in paths
    assert "/hub/secrets/refresh" in paths
    assert "/hub/indexer/since" in paths
    assert "/trades" in paths  # agent push
