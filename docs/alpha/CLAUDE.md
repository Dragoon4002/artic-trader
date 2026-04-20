# Alpha Docs — Module Guide

Authoritative spec for the **alpha** cut of Artic. When working on anything targeting alpha, load from here first. The parent `/docs/` tree still describes the *current* repo; alpha docs describe the *target* architecture.

## Load order

1. [project.md](project.md) — scope, user journey, beta line
2. [architecture.md](architecture.md) — diagram + component responsibilities
3. [system-map.md](system-map.md) — ownership, trust, call graph, ports
4. [data-model.md](data-model.md) — hub + user-server schemas
5. [api-contracts.md](api-contracts.md) — public + internal APIs
6. [runtime-flow.md](runtime-flow.md) — 12 lifecycle flows
7. [security-model.md](security-model.md) — auth, sandbox, secrets
8. [build-checklist.md](build-checklist.md) — delivery plan

## Plans (how-to-build)

| File | Scope |
|------|------|
| [plans/web-dashboard.md](plans/web-dashboard.md) | Next.js dashboard pages, features, UX |
| [plans/hub.md](plans/hub.md) | Hub internals, modules, crons |
| [plans/user-vm.md](plans/user-vm.md) | User-server + agent + VM lifecycle |
| [plans/connections.md](plans/connections.md) | Wire protocols between components |
| [morph-vm.md](morph-vm.md) | Morph Cloud as user-VM provider — 5 ops only (snapshot/start/launch/save/delete) |

## When to load what (alpha tasks)

| Task | Files |
|------|------|
| New hub endpoint | `api-contracts.md`, `system-map.md`, `plans/hub.md` |
| New user-server endpoint | `api-contracts.md`, `plans/user-vm.md`, `plans/connections.md` |
| Schema change | `data-model.md` (+ Alembic migration in code) |
| New service-to-service call | `plans/connections.md`, `system-map.md` (update both BEFORE code) |
| Dashboard feature | `plans/web-dashboard.md`, `api-contracts.md` |
| Credits / billing | `runtime-flow.md` §5, `data-model.md` credits tables |
| Sandbox / strategy exec | `security-model.md`, `plans/user-vm.md` strategy runner |
| VM lifecycle bug | `runtime-flow.md` §1 + §6, `plans/hub.md` vm module, `morph-vm.md` |
| Morph SDK / provider call | `morph-vm.md` |
| Chain signing | `plans/user-vm.md` chain module, `runtime-flow.md` §4 |

## Rules

- Every new call path updates `plans/connections.md` + `system-map.md` before code
- Every schema change updates `data-model.md` + an Alembic migration
- Cross-link between alpha docs; never duplicate content
- If a task falls under "beta graduation" in `project.md`, push back
- Current-repo docs (`/docs/project-brief.md`, `/docs/current-flow.md`) describe **today**; alpha docs describe **target** — don't conflate
