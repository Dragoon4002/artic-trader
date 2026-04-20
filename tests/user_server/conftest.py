"""Shared pytest fixtures for user-server tests.

Tests that need Postgres use the `USER_SERVER_TEST_DATABASE_URL` env var
(defaults to the dev-compose sidecar). If the URL is unreachable, tests
requiring it are skipped — matching `tasks/lessons.md` (no reliance on
implicit schema creation; Alembic is source of truth).
"""
from __future__ import annotations

import os

import pytest

DEFAULT_TEST_URL = "postgresql+psycopg2://artic:artic@localhost:15433/artic"


def _normalize(url: str) -> str:
    return url.replace("+asyncpg", "+psycopg2")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return _normalize(os.environ.get("USER_SERVER_TEST_DATABASE_URL", DEFAULT_TEST_URL))


@pytest.fixture(scope="session")
def require_pg(test_database_url: str) -> str:
    import sqlalchemy as sa

    try:
        eng = sa.create_engine(test_database_url, pool_pre_ping=True)
        with eng.connect() as c:
            c.execute(sa.text("SELECT 1"))
        eng.dispose()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Postgres unavailable at {test_database_url}: {exc}")
    return test_database_url
