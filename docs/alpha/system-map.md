# System Map — Alpha

Ownership, trust boundaries, call graph. Source of truth for "who talks to whom, and who is allowed to."

## Ownership matrix

| Resource | Writer | Readers | Storage |
|----------|--------|---------|---------|
| User accounts | hub (UPSERT on `/auth/verify`) | hub | hub Postgres; keyed by `(wallet_address, wallet_chain)` |
| `.init` username cache | hub (resolve at verify, refresh 24h) | hub, client (read via `/auth/me`) | hub Postgres (`users.init_username`) |
| Auth nonces | hub | hub | hub Postgres (`auth_nonce`, single-use, 5m TTL) |
| Session keys | hub (INSERT at `/auth/verify`) | hub | hub Postgres (`auth_session_keys`, pub key + last_nonce only) |
| User LLM/exchange keys (encrypted) | hub | hub (decrypt at VM wake) | hub Postgres (AES) |
| User VM state (on/off/snapshot) | hub | hub | hub Postgres + VM provider |
| Credit balance | hub | hub, client (read) | hub Postgres |
| Credit ledger | hub | hub | hub Postgres (append-only) |
| Market cache (candles) | hub APScheduler | hub, user-server (pull) | hub Postgres + in-memory |
| Live prices (Pyth) | — | agent, user-server | not stored |
| Marketplace strategy metadata | any user via hub | all | hub Postgres |
| Marketplace strategy code | publisher via hub | installers | hub object store + copied on install |
| Marketplace reports | any user via hub | hub, admin | hub Postgres |
| Indexer mirror (tx hashes) | hub (pull from user-server) | hub, other users via hub | hub Postgres |
| Agent config | user-server | user-server, agent (env at spawn) | user-server Postgres |
| Agent trades | user-server (from agent push) | user-server, hub (read via proxy) | user-server Postgres |
| Agent log entries | user-server (from agent push) | user-server, hub (read via proxy) | user-server Postgres |
| User strategies (own + installed) | user-server | user-server strategy runner | user-server Postgres |
| Local indexer (tx hashes) | user-server (on chain tx success) | user-server | user-server Postgres |
| Agent position (in-memory) | agent | agent | RAM only (lost on restart) |
| User-server chain wallet | hub funder (testnet) / user (beta) | user-server signer | VM keystore |

## Trust boundaries

```
[ External ]  client browser, market providers, LLM providers, chain RPC
      ↓
[ Hub boundary ]  all client→system traffic crosses here; hub authenticates + authorises
      ↓
[ User VM boundary ]  one VM per user; nothing crosses user VM boundaries laterally
      ↓
[ Process boundary ]  user-server ←→ agent over VM-internal network
      ↓
[ Sandbox boundary ]  user strategy code runs only inside RestrictedPython
```

Rules:
- Requests crossing the Hub boundary require JWT or API key
- Requests crossing the User VM boundary (hub → user-server) require mTLS + `X-Hub-Secret`
- Agent → user-server requires a per-spawn shared secret (`INTERNAL_SECRET`, injected as env)
- Strategy code never sees any secret, env, or network handle

## Call graph

| Caller | Callee | Protocol | Auth | Frequency |
|--------|--------|----------|------|-----------|
| client | hub `/auth/nonce` | HTTPS | — | on connect |
| client | hub `/auth/verify` | HTTPS | — (signature in body) | on connect |
| client | hub `/api/*` (GET) | HTTPS | JWT | user action |
| client | hub `/api/*` (POST/PATCH/DELETE) | HTTPS | JWT + session-key sig headers | user action |
| client | hub `/ws/*` | WSS | JWT | persistent |
| hub | user-server `*` | HTTPS proxy | mTLS + X-Hub-Secret | on client request |
| hub | VM provider API | HTTPS | provider token | wake/stop/snapshot |
| hub | market providers | HTTPS | API key | scheduler (60s) |
| hub | platform chain wallet | RPC | platform key | funder cron (5h) |
| user-server | hub `/api/market/*` | HTTPS | X-UserServer-Token | tick cadence (cached) |
| user-server | hub `/internal/indexer/flush` | HTTPS | X-UserServer-Token | 30min + pre-drain |
| user-server | hub `/internal/otel` | gRPC/HTTP | X-UserServer-Token | continuous |
| user-server | LLM provider | HTTPS | user's key (in memory) | strategy pick + supervisor |
| user-server | chain RPC | HTTPS | VM wallet | on trade + on supervisor |
| user-server | agent `:8000/*` | HTTP | INTERNAL_SECRET | spawn/start/stop/status |
| agent | user-server `/internal/*` | HTTP | INTERNAL_SECRET | every tick (status) / batched (logs) |
| agent | Pyth Hermes | HTTPS | none | every tick |

## Port map

| Service | Port | Exposure |
|---------|------|----------|
| Hub public API | 443 | internet |
| Hub WebSocket | 443 | internet |
| Hub internal receiver | 9001 | user-server only (mTLS) |
| User-server API | 8443 | hub only (mTLS) |
| Agent | 8000 | user VM internal |
| Postgres (hub) | 5432 | hub only |
| Postgres (user-server) | 5432 | user VM internal |

## Rules

- Clients never reach user-servers or agents directly
- User-servers never reach external market providers — route through hub cache
- Agent never calls anything except user-server + Pyth
- All cross-boundary calls carry auth — no "internal network = trusted" shortcuts
- New call path → update this doc **before** writing code (see `plans/connections.md`)
