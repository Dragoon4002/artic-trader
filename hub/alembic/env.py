"""Sync Alembic env. Rewrites DATABASE_URL driver +asyncpg -> +psycopg2."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool, text

from hub.db import models  # noqa: F401 — register model metadata
from hub.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_url = os.environ.get("DATABASE_URL", "")
if _url:
    # Render/Heroku give `postgres://…`; alembic + psycopg2 need a driver.
    if _url.startswith("postgres://"):
        _url = "postgresql://" + _url[len("postgres://"):]
    # asyncpg uses ?ssl=require; psycopg2 expects ?sslmode=require.
    # Neon (and most managed Postgres) requires SSL — translate so the same
    # DATABASE_URL works for runtime (asyncpg) and migrations (psycopg2).
    sync_url = _url.replace("+asyncpg", "+psycopg2")
    if sync_url.startswith("postgresql://") and "+psycopg2" not in sync_url:
        sync_url = "postgresql+psycopg2://" + sync_url[len("postgresql://"):]
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
    # Run schema-adoption on a SEPARATE connection with its own explicit
    # transaction. Otherwise SQLAlchemy 2.x leaves an autobegin transaction
    # open from `inspect()` calls, alembic nests under it, and when the
    # connection closes the whole stack rolls back silently. Bit us on Neon.
    with connectable.connect() as adopt_conn:
        with adopt_conn.begin():
            _adopt_existing_schema(adopt_conn)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


def _adopt_existing_schema(connection) -> None:
    # Render/Neon DBs were provisioned before alembic_version existed. If
    # core tables already exist but alembic has no recorded head, stamp the
    # latest revision so `upgrade head` is a no-op instead of re-CREATE.
    insp = inspect(connection)
    tables = set(insp.get_table_names())
    if "users" not in tables:
        return
    if "alembic_version" in tables:
        row = connection.execute(text("SELECT 1 FROM alembic_version LIMIT 1")).first()
        if row is not None:
            return
    else:
        connection.execute(
            text(
                "CREATE TABLE alembic_version ("
                "version_num VARCHAR(32) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            )
        )
    from alembic.script import ScriptDirectory

    head = ScriptDirectory.from_config(config).get_current_head()
    connection.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": head}
    )
    if hasattr(connection, "commit"):
        connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
