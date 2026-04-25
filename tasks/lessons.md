# Lessons

Durable patterns captured from past sessions. Review at session start when working on this repo.

## Python packaging — flat layout needs explicit discovery

- Pattern: a `pyproject.toml` for a flat-layout package (no `src/` dir) must declare package discovery explicitly, else `pip install -e .` installs nothing reachable.
- Symptom: `pip install -e ./pkg` succeeds silently; `import pkg` fails with `ModuleNotFoundError`.
- Fix (setuptools): add
  ```toml
  [tool.setuptools.packages.find]
  where = ["."]
  include = ["pkg*"]
  ```
  or set `package-dir` map explicitly.
- When to apply: any new pip-installable subpackage in this repo (e.g. `shared/`).
- Verify with `pip install -e ./pkg && python -c "from pkg import something"` **before** relying on imports downstream.

## Alembic env.py — sync even if the app is async

- Pattern: keep Alembic `env.py` synchronous even when the FastAPI app uses `create_async_engine`. Migrations run from shell, not the event loop.
- Bridge: rewrite driver in `env.py`:
  ```python
  db_url = os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg2")
  ```
- Consumer needs `psycopg2-binary` in requirements (migrations only).
- Reason: sync Alembic is the canonical pattern in every doc; async adds event-loop bootstrap you'll regret debugging at 2 AM.

## Docs discipline — update before code lands

- Rule: new service-to-service call → update `docs/alpha/plans/connections.md` + `docs/alpha/system-map.md` **in the same PR**.
- Rule: schema change → update `docs/alpha/data-model.md` + add Alembic migration in the same PR.
- Enforcement: `.github/workflows/docs-guard.yml` blocks PRs that violate.
- When tempted to skip: don't. The doc is the source of truth; code that drifts from it becomes untrustable.

## Morph VM shape

- Each user gets one Morph instance (paused when idle, 240s TTL → wake-on-HTTP).
- Inside the VM: Postgres 14 on rootfs (apt), dockerd on rootfs, user-server container, agent containers spawned by user-server via `docker.sock`.
- Hub is the only component holding `MORPH_API_KEY` — user-server and agents cannot self-snapshot or self-delete.
- Hub↔user-server auth: JWT over Morph-exposed HTTPS (no mTLS needed — Morph terminates TLS).
- `instance.snapshot()` before `instance.stop()` — order matters. Never stop without confirmed durable snapshot.

## Startup order — never assume schema exists

- Rule: FastAPI lifespan tasks (APScheduler jobs, background loops, price feeds) must not assume DB tables exist at startup.
- Why: `make dev` boots the app container before `make migrate` runs. First `make dev` on a fresh DB will fire all startup tasks against an empty schema → `ProgrammingError: relation "X" does not exist` flood.
- Pattern: gate each background task behind a `wait_for_schema(required_tables, timeout_s)` helper that polls `SELECT 1 FROM <t> LIMIT 0` with short backoff. Return normally on success; raise after timeout.
- Applies to: hub `price_feed_loop`, APScheduler jobs that touch tables, reconciliation loops.
- Alternative (worse): chain `migrate && up` in Makefile — slows every dev iteration and doesn't fix the durability issue (prod pods still crash-loop if schema drift).

## Today's repo vs alpha target

- `/docs/*.md` (non-alpha) describes **today's** code.
- `/docs/alpha/*.md` describes the **target** architecture.
- Don't modify today's docs while doing alpha work; don't assume current code matches alpha specs.
- Load `/docs/alpha/CLAUDE.md` first for any alpha task.
