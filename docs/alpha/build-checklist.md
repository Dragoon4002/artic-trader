# Alpha Build Checklist

Ordered by blocking dependencies. Each item maps to code deliverables and owning docs. Items within the same section can run in parallel.

## Phase 0 — Infra & foundations

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 0.1 | Pick VM provider (Firecracker/Fly Machines) — commit to API | — | [runtime-flow.md](runtime-flow.md#1-cold-wake) |
| 0.2 | Hub/user-server mTLS CA setup + cert mint pipeline | 0.1 | [security-model.md](security-model.md#hub--user-server) |
| 0.3 | Alembic migrations scaffold (hub + user-server) + CI check | — | [data-model.md](data-model.md) |
| 0.4 | OTel collector deployed; exporters stubbed in hub + user-server | — | [security-model.md](security-model.md#observability) |

## Phase 1 — Hub core

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 1.1a | Auth router (`/auth/nonce` + `/auth/verify` + `/auth/refresh` + `/auth/me`) — wallet-signature verifier, JWT issuance, refresh-cookie rotation | 0.3 | [api-contracts.md](api-contracts.md#auth), [security-model.md](security-model.md#auth) |
| 1.1b | Session keys: `auth_session_keys` table, `require_session_key` dep, monotonic-nonce sig verify, `/auth/session` list+revoke | 1.1a | [api-contracts.md](api-contracts.md#auth), [runtime-flow.md](runtime-flow.md#8a-session-key-authorized-action) |
| 1.1c | `.init` reverse lookup client + 24h cache on `users.init_username` | 1.1a | [project.md](project.md#initia-integrations-alpha) |
| 1.2 | `user_vms` table + provisioning on signup (create VM, stop, record) | 0.1, 0.3 | [runtime-flow.md](runtime-flow.md#8-signup--vm-provision) |
| 1.3 | Wake-proxy middleware: any `/api/v1/u/*` resumes VM then forwards | 0.1, 0.2, 1.2 | [runtime-flow.md](runtime-flow.md#1-cold-wake) |
| 1.4 | Scale-to-zero drain cron (5min idle) | 1.3 | [runtime-flow.md](runtime-flow.md#6-scale-to-zero-drain) |
| 1.5 | Market cache + APScheduler refresh (TwelveData + Pyth proxy) | 0.3 | [api-contracts.md](api-contracts.md#market-data) |
| 1.6 | Secrets encryption + `/hub/secrets/refresh` push to user-server on wake | 1.3 | [security-model.md](security-model.md#secrets) |

## Phase 2 — User-server + agent image

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 2.1 | User-server scaffold (FastAPI + Postgres + migrations) | 0.3 | [plans/user-vm.md](plans/user-vm.md) |
| 2.2 | Agent CRUD + start/stop via docker SDK (VM-internal) | 2.1 | [runtime-flow.md](runtime-flow.md#3-agent-create--start) |
| 2.3 | Agent image refactor: remove LLM SDKs + API key env | 2.1 | [plans/user-vm.md](plans/user-vm.md) |
| 2.4 | LLM proxy in user-server (`/llm/plan`, `/llm/supervise`, `/llm/chat`) | 2.1, 1.6 | [api-contracts.md](api-contracts.md#llm-proxy) |
| 2.5 | Agent tick loop calls user-server for signals, LLM, chain | 2.2, 2.4 | [runtime-flow.md](runtime-flow.md#2-tick-loop) |
| 2.6 | Chain signer module in user-server (TradeLogger + DecisionLogger calls) | 2.1 | [runtime-flow.md](runtime-flow.md#4-trade--chain-log--indexer) |
| 2.7 | Local indexer table + writer on tx success | 2.6 | [data-model.md](data-model.md#indexer_tx-local) |

## Phase 3 — Strategy system

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 3.1 | RestrictedPython runner module + whitelist + timeouts | 2.1 | [security-model.md](security-model.md#strategy-sandbox) |
| 3.2 | Strategy dispatcher: builtin + authored + marketplace | 3.1, 2.5 | [plans/user-vm.md](plans/user-vm.md) |
| 3.3 | Hub marketplace tables + public CRUD | 0.3, 1.1 | [data-model.md](data-model.md#marketplace_strategy) |
| 3.4 | Install flow (hub → user-server copy) | 3.2, 3.3 | [runtime-flow.md](runtime-flow.md#10-marketplace-install) |
| 3.5 | Report/delist + 3-in-7-days auto-hide | 3.3 | [runtime-flow.md](runtime-flow.md#11-marketplace-report) |

## Phase 4 — Billing + indexer mirror

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 4.1 | Credits + credit_ledger tables | 0.3 | [data-model.md](data-model.md#credits) |
| 4.2 | Per-minute debit cron; halt on zero | 4.1, 1.3 | [runtime-flow.md](runtime-flow.md#5-credit-debit-cron-hub-every-minute) |
| 4.3 | Admin grant endpoint + CLI | 4.1 | [api-contracts.md](api-contracts.md#credits) |
| 4.4 | Indexer pull sync cron (30min) | 1.3, 2.7 | [runtime-flow.md](runtime-flow.md#9-indexer-pull-sync-hub--user-server-30min) |
| 4.5 | Pre-drain flush integration | 1.4, 2.7 | [runtime-flow.md](runtime-flow.md#6-scale-to-zero-drain) |
| 4.6 | Hub indexer query endpoints (`/indexer/tx`) | 4.4 | [api-contracts.md](api-contracts.md#indexer-read-across-all-users) |

## Phase 5 — Chain funder

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 5.1 | Platform hot wallet provisioned on testnet | — | [plans/hub.md](plans/hub.md) |
| 5.2 | Funder cron (5h, configurable floor/topup) | 5.1, 1.2 | [runtime-flow.md](runtime-flow.md#7-platform-wallet-funder-testnet) |
| 5.3 | Low-balance alert + metric | 5.2 | [security-model.md](security-model.md#observability) |

## Phase 6 — Web dashboard

| # | Item | Depends on | Doc refs |
|---|------|-----------|----------|
| 6.1 | Auth pages (signup/login) | 1.1 | [plans/web-dashboard.md](plans/web-dashboard.md) |
| 6.2 | Agents list + detail + create/start/stop wizard | 1.3, 2.2 | [plans/web-dashboard.md](plans/web-dashboard.md) |
| 6.3 | Live log + status via WebSocket | 1.3 | [plans/web-dashboard.md](plans/web-dashboard.md) |
| 6.4 | Strategy marketplace browse + install + report | 3.3, 3.4 | [plans/web-dashboard.md](plans/web-dashboard.md) |
| 6.5 | Credits widget + ledger view | 4.1 | [plans/web-dashboard.md](plans/web-dashboard.md) |
| 6.6 | "Warming up" cold-wake UX | 1.3 | [plans/web-dashboard.md](plans/web-dashboard.md) |
| 6.7 | Indexer explorer (per-user + cross-user) | 4.6 | [plans/web-dashboard.md](plans/web-dashboard.md) |

## Phase 7 — Hardening for 100-user alpha

| # | Item | Depends on |
|---|------|-----------|
| 7.1 | Rate limits on hub | 1.1 |
| 7.2 | Audit log table + hooks | 1.1 |
| 7.3 | Error shape standardisation + client handling | all |
| 7.4 | End-to-end test: create→start→trade→snapshot→wake→resume | all |
| 7.5 | Load test: 100 concurrent dashboards, 300 alive agents | all |
| 7.6 | Runbook: VM wake failure, funder failure, credits halt storm | all |

## Explicitly out (defer to beta)

- HashKey live executor
- Mainnet
- Stripe / on-chain payments
- VM spec tiers / upgrades
- Warm pool for signup
- TUI / CLI / Telegram clients
- User-server rolling-upgrade operator
- HSM / MPC wallet
- WAF / DDoS edge
