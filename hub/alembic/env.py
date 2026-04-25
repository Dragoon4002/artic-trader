"""Sync Alembic env. Rewrites DATABASE_URL driver +asyncpg -> +psycopg2."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from hub.db import models  # noqa: F401 — register model metadata
from hub.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_url = os.environ.get("DATABASE_URL", "")
if _url:
    # asyncpg uses ?ssl=require; psycopg2 expects ?sslmode=require.
    # Neon (and most managed Postgres) requires SSL — translate so the same
    # DATABASE_URL works for runtime (asyncpg) and migrations (psycopg2).
    sync_url = _url.replace("+asyncpg", "+psycopg2")
    if "?" in sync_url:
        base, _, qs = sync_url.partition("?")
        params = []
        for kv in qs.split("&"):
            if not kv:
                continue
            k, _eq, v = kv.partition("=")
            if k == "ssl":
                params.append(f"sslmode={v}")
            else:
                params.append(kv)
        sync_url = base + "?" + "&".join(params)
    config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
