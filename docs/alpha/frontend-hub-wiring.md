# Frontend ↔ Hub Wiring

Authoritative map of every dashboard data dependency → hub endpoint. Use this when swapping `clients/web/lib/api.ts` from demo fixtures to real `fetch`. Every row is grounded in committed code, not spec aspiration.

> **Scope**: `main` branch, post VM v0 merges (`527e527` … `9f04c8a`). Dashboard is the wallet-auth version (not the removed `feat/web` email-pwd version).

---

## 1 · Hub endpoints — mounted today

Source of truth: `grep include_router hub/server.py` + every `APIRouter(prefix=…)` in `hub/`.

| Method | Path | Auth | File | Status |
|---|---|---|---|---|
| **Auth (client-facing)** |
| POST | `/auth/nonce` | none | [hub/auth/router.py:79](hub/auth/router.py#L79) | live |
| POST | `/auth/verify` | none | [hub/auth/router.py:115](hub/auth/router.py#L115) | live — mints JWT + session key + `user_vms` row |
| POST | `/auth/refresh` | refresh cookie | [hub/auth/router.py:225](hub/auth/router.py#L225) | live |
| GET | `/auth/me` | Bearer JWT | [hub/auth/router.py:244](hub/auth/router.py#L244) | live |
| GET | `/auth/session` | Bearer JWT | [hub/auth/router.py:264](hub/auth/router.py#L264) | live |
| DELETE | `/auth/session` | session-key headers | [hub/auth/router.py:286](hub/auth/router.py#L286) | live |
| POST | `/api/keys` | session-key headers | [hub/auth/router.py:311](hub/auth/router.py#L311) | live |
| **Market (client-facing, no auth)** |
| GET | `/api/market/price/{symbol}` | none | [hub/market/router.py:16](hub/market/router.py#L16) | live (Pyth) |
| GET | `/api/market/prices` | none | [hub/market/router.py:28](hub/market/router.py#L28) | live |
| GET | `/api/market/candles` | none | [hub/market/router.py:33](hub/market/router.py#L33) | live (TwelveData; needs `TWELVE_DATA_API_KEY`) |
| **Secrets (client-facing)** |
| POST | `/api/v1/secrets` | Bearer JWT | [hub/secrets/service.py:28](hub/secrets/service.py#L28) | live |
| GET | `/api/v1/secrets` | Bearer JWT | [hub/secrets/service.py:55](hub/secrets/service.py#L55) | live |
| DELETE | `/api/v1/secrets/{key_name}` | Bearer JWT | [hub/secrets/service.py:69](hub/secrets/service.py#L69) | live |
| **User-scoped proxy (client-facing, wake + forward to user-server)** |
| ANY | `/api/v1/u/{anything}` | Bearer JWT | [hub/proxy/middleware.py:33](hub/proxy/middleware.py#L33) | live — rewrites `/api/v1/u/foo` → `<vm-endpoint>/foo` w/ `X-Hub-Secret` |
| **Images (hub → Morph VM)** |
| GET | `/internal/v1/images/{name}` | `X-Hub-Secret` | [hub/internal/images.py:42](hub/internal/images.py#L42) | live — serves `.tar.gz` from `hub/docker/images/` |
| GET | `/internal/v1/images` | `X-Hub-Secret` | [hub/internal/images.py:60](hub/internal/images.py#L60) | live |
| **Internal (user-server → hub)** |
| POST | `/internal/v1/credits/heartbeat` | `X-UserServer-Token` | [hub/internal/router.py:26](hub/internal/router.py#L26) | stub: `{ok,noop}` |
| POST | `/internal/v1/indexer/flush` | `X-UserServer-Token` | [hub/internal/router.py:33](hub/internal/router.py#L33) | stub |
| POST | `/internal/v1/otel/spans` | `X-UserServer-Token` | [hub/internal/router.py:40](hub/internal/router.py#L40) | stub |
| **WebSocket (hub-direct)** |
| WS | `/ws/prices` | none | [hub/ws/broadcaster.py](hub/ws/broadcaster.py) | live — price_feed_loop broadcasts |
| WS | `/ws/agents/{id}/status` | — | [hub/ws/broadcaster.py](hub/ws/broadcaster.py) | live (deprecated agent source) |
| WS | `/ws/agents/{id}/logs` | — | [hub/ws/broadcaster.py](hub/ws/broadcaster.py) | live (deprecated agent source) |
| **WebSocket proxy (hub → user-server)** |
| WS | `/ws/u/agents/{id}/status` | none | [hub/proxy/ws.py:15](hub/proxy/ws.py#L15) | **stub — closes w/ 1011** |
| WS | `/ws/u/agents/{id}/logs` | none | [hub/proxy/ws.py:24](hub/proxy/ws.py#L24) | **stub** |
| **Health** |
| GET | `/health` | none | [hub/server.py:113](hub/server.py#L113) | live |
| GET | `/health/ready` | none | [hub/server.py:118](hub/server.py#L118) | live — checks DB |

### NOT mounted (scaffolded, README only)

| Module | Planned path | What exists | Spec ref |
|---|---|---|---|
| `hub/credits/` | `GET /api/v1/credits`, `/credits/ledger` | README only | api-contracts.md §Credits |
| `hub/marketplace/` | `GET /marketplace*`, `POST /marketplace/{id}/{install,report}` | README only | api-contracts.md §Marketplace |
| `hub/indexer/` | `GET /indexer/tx*` | README only | api-contracts.md §Indexer |
| `hub/admin/` | `POST /admin/marketplace/{id}/delist` | README only | spec line |
| `hub/funder/` | n/a (internal cron) | README only | — |
| `hub/audit/` | n/a (internal) | `service.py` stub | — |
| Deprecated | `/api/agents/*` (CRUD) | `hub/deprecated/agents/router.py` exists, **not mounted** | moves to user-server per alpha spec |
| Leaderboard | `/api/leaderboard` | exists in deprecated router, not mounted | legacy feature; not in alpha api-contracts.md |

### User-server endpoints reachable through `/api/v1/u/*` proxy

All mounted in [user-server/user_server/server.py](user-server/user_server/server.py). Hub proxy strips the `/api/v1/u` prefix → forwards to these paths.

| Dashboard call | Hub proxy rewrites to | User-server file |
|---|---|---|
| `GET /api/v1/u/agents` | `GET /agents` | [agents/router.py](user-server/user_server/agents/router.py) |
| `POST /api/v1/u/agents` | `POST /agents` (creates, status=stopped) | ↑ |
| `GET /api/v1/u/agents/{id}` | `GET /agents/{id}` | ↑ |
| `DELETE /api/v1/u/agents/{id}` | `DELETE /agents/{id}` | ↑ |
| `POST /api/v1/u/agents/{id}/start` | `POST /agents/{id}/start` | ↑ |
| `POST /api/v1/u/agents/{id}/stop` | `POST /agents/{id}/stop` | ↑ |
| `POST /api/v1/u/agents/start-all` | `POST /agents/start-all` | ↑ |
| `POST /api/v1/u/agents/stop-all` | `POST /agents/stop-all` | ↑ |
| `GET /api/v1/u/strategies` | `GET /strategies` | [strategies/router.py](user-server/user_server/strategies/router.py) |
| `POST /api/v1/u/strategies` | `POST /strategies` | ↑ |
| `DELETE /api/v1/u/strategies/{id}` | `DELETE /strategies/{id}` | ↑ |
| `POST /api/v1/u/llm/*` | `POST /llm/*` | [llm/router.py](user-server/user_server/llm/router.py) |
| `GET /api/v1/u/indexer/local*` | `GET /indexer/local*` | [indexer/router.py](user-server/user_server/indexer/router.py) |

**Agent trade/log reads do not exist yet on user-server** — `GET /agents/{id}/trades` and `/logs` are in spec but not in [user-server/agents/router.py](user-server/user_server/agents/router.py). Tracked in §4 gaps.

---

## 2 · Dashboard consumers — `lib/api.ts`

`clients/web/lib/api.ts` is a 14-function wrapper, each returning demo data. Swap body-for-body to `fetch`; React Query hooks and page components don't change.

| Function | Current source | Real endpoint | Auth |
|---|---|---|---|
| `listAgents()` | `demoAgents` | `GET /api/v1/u/agents` | Bearer |
| `getAgent(id)` | demoAgents.find | `GET /api/v1/u/agents/{id}` | Bearer |
| `listTrades(agentId?)` | `demoTrades` | `GET /api/v1/u/agents/{id}/trades` | Bearer — **user-server route missing** |
| `listLogs(agentId)` | `demoLogs` | `GET /api/v1/u/agents/{id}/logs?limit=200` | Bearer — **user-server route missing** |
| `listStrategies()` | demo | `GET /api/v1/u/strategies` (split installed/authored client-side by `source`) | Bearer |
| `listMarketplace(sort)` | demo | `GET /marketplace?sort=…` | Bearer — **hub route missing** |
| `getMarketplaceItem(id)` | demo | `GET /marketplace/{id}` | Bearer — **hub route missing** |
| `getCredits()` | demo | `GET /credits` | Bearer — **hub route missing** |
| `listLedger()` | demo | `GET /credits/ledger?limit=100` | Bearer — **hub route missing** |
| `listIndexer(filter)` | demo | `GET /indexer/tx?...` | Bearer — **hub route missing** |
| `listSessions()` | demo | `GET /auth/session` | Bearer |
| `getApiKeyHint()` | demo | no endpoint — embed in `/auth/me` or new `/api/keys/hint` | — |

No mutation helpers yet. For v0 spawn-only, we need to add:
- `createAgent(body)` → `POST /api/v1/u/agents`
- `startAgent(id)` → `POST /api/v1/u/agents/{id}/start`
- `stopAgent(id)` → `POST /api/v1/u/agents/{id}/stop`
- `deleteAgent(id)` → `DELETE /api/v1/u/agents/{id}`
- `stopAllAgents()` → `POST /api/v1/u/agents/stop-all`

---

## 3 · Per-page wire-up plan

Order by complexity of dependency. Each row ships independently.

| Page | Reads | Writes | Blocking hub work | Complexity |
|---|---|---|---|---|
| `/app/agents` (list) | `listAgents`, `listTrades` (for PnL) | — | none (all proxied) | **L** |
| `/app/agents/new` | — | `createAgent` + optional `startAgent` | none | **L** |
| `/app/agents/[id]` | `getAgent`, `listTrades(id)`, `listLogs(id)` + `/ws/u/agents/{id}/{status,logs}` | `startAgent`, `stopAgent`, `deleteAgent` | user-server `/agents/{id}/{trades,logs}`, hub WS proxy | **M** |
| `/app/strategies` | `listStrategies` | `POST /api/v1/u/strategies`, `DELETE /api/v1/u/strategies/{id}` | none | **L** |
| `/app/settings` (sessions) | `listSessions` | `DELETE /auth/session` (session-key) | session-key header derivation in dashboard | **M** |
| `/app/settings` (api key) | `getApiKeyHint` | `POST /api/keys` (session-key) | derivation path + hub hint endpoint | **M** |
| `/app/settings` (LLM keys) | `GET /api/v1/secrets` | `POST /api/v1/secrets`, `DELETE /api/v1/secrets/{name}` | none | **L** |
| `/app/credits` | `getCredits`, `listLedger` | — | **hub/credits/ router** | **H** (gap) |
| `/app/indexer` | `listIndexer` | — | **hub/indexer/ router** | **H** (gap) |
| `/app/marketplace` | `listMarketplace`, `getMarketplaceItem` | install, report, publish mutations | **hub/marketplace/ router** | **H** (gap) |
| `/app/onboarding` | derived from `/auth/me` + agents list | — | none | **L** |

---

## 4 · Gaps that block full wire-up

### 4a · Missing hub routers (dashboard has NO endpoint to call)

| Gap | Dashboard page | Effort |
|---|---|---|
| `hub/credits/router.py` — `GET /credits`, `GET /credits/ledger` | /app/credits | ~0.5d |
| `hub/marketplace/router.py` — list/detail/publish/install/report | /app/marketplace | ~1.5d (code blob storage + report unique constraint + install → user-server copy) |
| `hub/indexer/router.py` — `GET /indexer/tx` w/ filters | /app/indexer | ~1d (query builder on `indexer_tx_mirror`) |
| `hub/admin/router.py` — `POST /admin/marketplace/{id}/delist` | (admin only, later) | skip for v0 |

**None of the above have models wired to migrations either** — need migration `0004_credits_marketplace_indexer.py` for `credits`, `credit_ledger`, `marketplace_strategy`, `marketplace_report`, `indexer_tx_mirror` tables before routers can query.

### 4b · Missing user-server endpoints

| Gap | Dashboard page | Effort |
|---|---|---|
| `GET /agents/{id}/trades` | agent detail | ~0.25d (query `trades` table by `agent_id`) |
| `GET /agents/{id}/logs` | agent detail | ~0.25d (query `log_entries` table) |

### 4c · Missing infrastructure

| Gap | Impact | Effort |
|---|---|---|
| `/ws/u/agents/{id}/status` frame-forward | agent detail live updates | ~1d (hub proxy_ws.py real impl + user-server WS emit) |
| Session-key header derivation in dashboard | /auth/session DELETE, /api/keys POST | ~0.5d (add `signedFetch` helper in `lib/api.ts`; uses `autoSign` / sessionkey on every mutation) |
| `getApiKeyHint` endpoint | settings page | ~0.1d (return last 4 chars of api_key_hash from /auth/me) |

### 4d · Path/prefix drift

| Spec | Code | Decision needed |
|---|---|---|
| `/api/v1/market/*` (spec) | `/api/market/*` (code) | pick one; update the other |
| `/api/v1/secrets` (code) | `/api/v1/settings/api-keys` (onboarding stub) | unify; dashboard onboarding already uses this path with stub response |

### 4e · Not wired (but not blocking)

- Notifications WS `/ws/notifications` — in dashboard plan doc, never built
- LLM proxy `/api/v1/u/llm/*` — works through proxy, dashboard has no UI yet
- Mobile responsive — beta

---

## 5 · Wiring execution order

Minimum code to bring the dashboard to **live hub data** (not just spawn-only).

### Phase A — Foundation (~0.5d, no hub changes)

1. `lib/api.ts`: add `bearerHeader()` helper reading JWT from wallet-auth context
2. `lib/api.ts`: add `signedFetch(url, init)` helper that derives session-key headers via `useWallet().autoSign` for mutations
3. `lib/api.ts`: swap 6 functions that hit currently-live endpoints — `listAgents`, `getAgent`, `listStrategies`, `listSessions`, LLM-secrets CRUD (new). Keep demo fallback behind `NEXT_PUBLIC_USE_DEMO=1` for offline dev.
4. Add `createAgent`, `startAgent`, `stopAgent`, `deleteAgent` mutations.
5. `/app/agents/new` wire POST → redirect to `/app/agents/{id}`. Replace `PendingHub` placeholder.

**After Phase A**: spawn-only flow works end-to-end (the v0 goal).

### Phase B — Agent detail (~1.5d, modest user-server work)

1. User-server: add `GET /agents/{id}/trades` and `/logs` (direct DB reads, paginated).
2. `lib/api.ts`: swap `listTrades`, `listLogs` to real.
3. Hub: implement `/ws/u/agents/{id}/status` proxy frame-forward. User-server emits status frames every N ticks.
4. Dashboard: wire `useWebSocket('/ws/u/agents/{id}/status')` replacing poll.

### Phase C — Credits (~1d hub, ~0.2d dashboard)

1. Migration `0004` adds `credits`, `credit_ledger`.
2. `hub/credits/router.py` + `service.py` — balance query, ledger pagination.
3. `hub/credits/debit_cron.py` — debit alive agents per minute (can ship empty-tick version first).
4. `lib/api.ts`: swap `getCredits`, `listLedger`.

### Phase D — Indexer (~1d hub, ~0.2d dashboard)

1. Migration `0004` adds `indexer_tx_mirror` (may land with C).
2. `hub/indexer/router.py` query builder.
3. `lib/api.ts`: swap `listIndexer`.
4. Defer pull-sync cron — indexer_tx_mirror stays empty until chain layer produces rows.

### Phase E — Marketplace (~1.5d hub, ~0.5d dashboard)

1. Migration adds `marketplace_strategy`, `marketplace_report`.
2. `hub/marketplace/router.py` — list/detail/publish/install/report.
3. Install path: hub calls user-server `POST /strategies` with `code_blob` (reuses existing user-server route).
4. `lib/api.ts`: swap `listMarketplace`, `getMarketplaceItem` + add publish/install/report mutations.

### Phase F — Polish

- WS `/ws/notifications` (credits threshold, agent halted)
- Cold-wake UX — React Query interceptor catches 202 `VM_WAKING`, shows overlay, retries
- Path prefix cleanup `/api/market` ↔ `/api/v1/market`
- Deprecated `hub/deprecated/` cleanup after all zones verified

---

## 6 · Invariants (don't break)

1. All client→hub calls include `Authorization: Bearer <jwt>` OR use refresh cookie; no API key in browser.
2. Mutations (`POST`, `PATCH`, `DELETE`) under `/auth/session`, `/api/keys`, and any future write path require session-key headers (`X-Session-Id`, `X-Session-Nonce`, `X-Session-Sig`). Read-only calls don't.
3. `/api/v1/u/*` is a wildcard proxy — never add a real hub route under that prefix; it always hits the user VM.
4. Proxy strips `/api/v1/u` before forwarding. User-server routes mount without prefix.
5. `X-Hub-Secret` is a hub↔user-server internal header. Never send it from the browser.
6. Dashboard `lib/api.ts` contract stays stable — only function bodies change. Hooks / components untouched.
7. Cold-wake 202 handling is centralised in `lib/api.ts` — individual pages don't retry.

---

## 7 · Environment vars to populate before wiring

Dashboard:
```env
NEXT_PUBLIC_HUB_URL=http://localhost:9000   # dev
NEXT_PUBLIC_USE_DEMO=0                      # set 1 to keep demo fixtures
```

Hub (already in `.env.dev.example`):
```env
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=...
INTERNAL_SECRET=...          # also used as X-Hub-Secret
MORPH_API_KEY=...
MORPH_GOLDEN_SNAPSHOT_ID=... # paste after build_golden_snapshot.py run
HUB_PUBLIC_URL=...           # Morph VM must reach this
TWELVE_DATA_API_KEY=...      # optional: enables /api/market/candles
```

---

## 8 · Open questions before coding Phase A

1. **Path prefix**: keep `/api/market/*` or migrate to `/api/v1/market/*` to match spec? (recommend: migrate — one grep, refactor, done)
2. **LLM secrets on settings page**: use `/api/v1/secrets` (implemented) or add `/settings/api-keys` alias to match onboarding step? (recommend: unify on `/api/v1/secrets`)
3. **Demo fallback**: keep `NEXT_PUBLIC_USE_DEMO=1` support in `lib/api.ts` indefinitely (handy for offline dev / storybook) or rip it out once hub is up? (recommend: keep via env flag)
4. **Agent `/trades` + `/logs` pagination shape**: cursor or offset? (recommend: offset for v0, cursor in beta)
5. **Credits granularity**: debit per tick (current spec) or per minute rollup (less IO)? (recommend: per-minute for alpha to avoid row explosion)
