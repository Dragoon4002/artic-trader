"""ONE-SHOT: drop & recreate the public schema, then exit. Used to wipe a
half-applied alembic state before re-running migrations from scratch.

DO NOT call this from normal deploys — it destroys all data.
"""

from __future__ import annotations

import os
import re
import sys

import psycopg2


def normalize_for_psycopg2(url: str) -> str:
    """Convert any of {postgres://, postgresql://, postgresql+asyncpg://,
    postgresql+psycopg2://} to a plain `postgresql://...` DSN psycopg2 accepts."""
    # Strip explicit driver suffix.
    url = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", url)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def main() -> int:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        print("DATABASE_URL is empty", file=sys.stderr)
        return 2
    dsn = normalize_for_psycopg2(raw).split("?", 1)[0]
    conn = psycopg2.connect(dsn, sslmode="require")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
    print("schema public dropped + recreated")
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
