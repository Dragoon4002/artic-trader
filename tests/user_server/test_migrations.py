"""Alembic round-trip: upgrade -> downgrade -> upgrade on a clean schema.

Runs against `USER_SERVER_TEST_DATABASE_URL` (defaults to dev-compose sidecar
on localhost:15433). Each test wipes the public schema first — serial only.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "user-server" / "alembic.ini"
EXPECTED = {"agents", "trades", "log_entries", "strategies", "indexer_tx", "alembic_version"}


def _alembic_cfg() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "user-server" / "alembic"))
    return cfg


@pytest.fixture
def clean_schema(require_pg: str):
    eng = sa.create_engine(require_pg)
    with eng.begin() as c:
        c.execute(sa.text("DROP SCHEMA public CASCADE"))
        c.execute(sa.text("CREATE SCHEMA public"))
    eng.dispose()
    os.environ["DATABASE_URL"] = require_pg
    yield require_pg
    os.environ.pop("DATABASE_URL", None)


def _tables() -> set[str]:
    eng = sa.create_engine(os.environ["DATABASE_URL"])
    try:
        return set(sa.inspect(eng).get_table_names(schema="public"))
    finally:
        eng.dispose()


def test_upgrade_head_creates_all_tables(clean_schema):
    command.upgrade(_alembic_cfg(), "head")
    assert EXPECTED.issubset(_tables()), f"missing {EXPECTED - _tables()}"


def test_downgrade_roundtrip(clean_schema):
    cfg = _alembic_cfg()
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0001")
    remaining = _tables() & {"agents", "trades", "log_entries", "strategies", "indexer_tx"}
    assert remaining == set(), f"leftover {remaining}"
    command.upgrade(cfg, "head")
    assert EXPECTED.issubset(_tables())
