# Artic Alpha — Docs Index

Authoritative spec for the alpha cut. Read top-to-bottom if new to the project.

## Read order

1. [project.md](project.md) — what Artic alpha is, user journey, scope, beta line
2. [architecture.md](architecture.md) — one-page diagram + component responsibilities
3. [system-map.md](system-map.md) — ownership matrix, trust boundaries, call graph, ports
4. [data-model.md](data-model.md) — hub + user-server Postgres schemas
5. [api-contracts.md](api-contracts.md) — public + internal API surfaces
6. [runtime-flow.md](runtime-flow.md) — every lifecycle path (wake, tick, drain, cron jobs)
7. [security-model.md](security-model.md) — auth, sandbox, secrets, rate limits, threat model
8. [build-checklist.md](build-checklist.md) — ordered delivery plan for alpha

## Plans (implementation-focused)

9. [plans/web-dashboard.md](plans/web-dashboard.md) — web UI pages, features, UX
10. [plans/hub.md](plans/hub.md) — hub server internals and modules
11. [plans/user-vm.md](plans/user-vm.md) — user VM + user-server + agent internals
12. [plans/connections.md](plans/connections.md) — wire protocols between components
13. [morph-vm.md](morph-vm.md) — Morph Cloud as user-VM provider (snapshot/start/launch/save/delete)

## Conventions

- Tables > prose for specs
- Every new call path updates [system-map.md](system-map.md) **before** code lands
- Every schema change updates [data-model.md](data-model.md) + Alembic migration
- Nothing in this folder duplicates content — cross-link instead
- When reality diverges from a doc: fix the doc in the same PR

## Scope guard

If a change request falls under "beta" in [project.md](project.md#beta-graduation-criteria), push back. Alpha is narrow on purpose.
