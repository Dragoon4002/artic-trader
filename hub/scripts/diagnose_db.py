"""Diagnostic: connect with both psycopg2 and asyncpg to the *same*
DATABASE_URL, print which DB / schema / tables each sees. If they disagree,
we have a routing/branch issue."""

from __future__ import annotations

import asyncio
import os
import re
import sys

import asyncpg
import psycopg2


def to_psycopg2(url: str) -> str:
    url = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", url)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url.split("?", 1)[0]


def to_asyncpg(url: str) -> str:
    # asyncpg accepts plain `postgresql://` (or `postgres://`); strip driver suffix.
    url = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", url)
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def via_psycopg2(url: str) -> dict:
    conn = psycopg2.connect(to_psycopg2(url), sslmode="require")
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_user, current_setting('search_path')")
    db, user, sp = cur.fetchone()
    cur.execute(
        "SELECT schemaname, tablename FROM pg_tables "
        "WHERE schemaname NOT IN ('pg_catalog','information_schema') "
        "ORDER BY schemaname, tablename"
    )
    tables = [f"{r[0]}.{r[1]}" for r in cur.fetchall()]
    cur.execute("SELECT inet_server_addr()::text, inet_server_port()")
    host, port = cur.fetchone()
    conn.close()
    return {"db": db, "user": user, "search_path": sp, "host": host, "port": port, "tables": tables}


async def via_asyncpg(url: str) -> dict:
    conn = await asyncpg.connect(to_asyncpg(url), ssl="require")
    db = await conn.fetchval("SELECT current_database()")
    user = await conn.fetchval("SELECT current_user")
    sp = await conn.fetchval("SELECT current_setting('search_path')")
    rows = await conn.fetch(
        "SELECT schemaname, tablename FROM pg_tables "
        "WHERE schemaname NOT IN ('pg_catalog','information_schema') "
        "ORDER BY schemaname, tablename"
    )
    tables = [f"{r['schemaname']}.{r['tablename']}" for r in rows]
    host = await conn.fetchval("SELECT inet_server_addr()::text")
    port = await conn.fetchval("SELECT inet_server_port()")
    await conn.close()
    return {"db": db, "user": user, "search_path": sp, "host": host, "port": port, "tables": tables}


def main() -> int:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL is empty", file=sys.stderr)
        return 2

    print("── DB DIAGNOSTIC ──")
    # Mask password before printing.
    masked = re.sub(r"://([^:]+):[^@]+@", r"://\1:***@", url)
    print(f"DATABASE_URL = {masked}")

    p = via_psycopg2(url)
    a = asyncio.run(via_asyncpg(url))

    print(f"psycopg2  → db={p['db']} user={p['user']} host={p['host']}:{p['port']} search_path={p['search_path']}")
    print(f"            tables ({len(p['tables'])}): {p['tables']}")

    # Also report alembic_version if it exists anywhere.
    try:
        conn2 = psycopg2.connect(to_psycopg2(url), sslmode="require")
        cur2 = conn2.cursor()
        cur2.execute(
            "SELECT schemaname FROM pg_tables WHERE tablename='alembic_version'"
        )
        for (schema,) in cur2.fetchall():
            cur2.execute(f'SELECT version_num FROM "{schema}".alembic_version')
            for (v,) in cur2.fetchall():
                print(f"            alembic_version[{schema}] = {v}")
        conn2.close()
    except Exception as e:
        print(f"            alembic_version probe failed: {e}")
    print(f"asyncpg   → db={a['db']} user={a['user']} host={a['host']}:{a['port']} search_path={a['search_path']}")
    print(f"            tables ({len(a['tables'])}): {a['tables']}")

    same = (p["db"] == a["db"] and set(p["tables"]) == set(a["tables"]))
    print(f"identical view: {same}")
    if not same:
        print("DRIVERS SEE DIFFERENT STATE — likely Neon branch / pooler routing", file=sys.stderr)
        return 1
    if not any("user_vms" in t for t in p["tables"]):
        print("user_vms missing from BOTH views — migrations not applied", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
