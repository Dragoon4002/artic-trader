# Plan — Central Hub

Single persistent Python server. All client traffic goes through here. Owns cross-user state, routing, billing, market cache, observability.

## Responsibilities

| Area | What hub does | What hub does **not** do |
|------|--------------|--------------------------|
| Auth | verify wallet signature (chain-pluggable), issue JWT + session key, verify session-key sigs on mutations, resolve `.init` | store decrypted LLM keys on disk; hold session private keys |
| Routing | proxy `/api/v1/u/*` to user-server; cold-wake | execute user strategy code |
| Credits | ledger, debit cron, halt trigger | call chain / sign txs |
| Market cache | TwelveData refresh, Pyth proxy, cache reads | per-user market storage |
| Marketplace | strategy CRUD, reports, auto-delist | run strategies |
| Indexer mirror | pull-sync from user-servers, cross-user read API | write to chain |
| Funder | fund user-server wallets on testnet | mainnet signing (beta) |
| Observability | OTel collector, dashboards | per-VM logs on-disk |

## Module structure

```
hub/
├── server.py                 # FastAPI app factory, middleware, lifespan
├── config.py                 # pydantic-settings (env only)
├── db/
│   ├── base.py               # async engine, session factory
│   ├── migrations/           # Alembic (mandatory)
│   └── models/               # users, user_vms, credits, ledger, marketplace, …
│
├── auth/
│   ├── router.py             # /auth/nonce, /auth/verify, /auth/refresh, /auth/me, /auth/session
│   ├── service.py            # nonce gen, message build, JWT issue/verify
│   ├── session.py            # issue/verify/revoke session keys; monotonic-nonce guard
│   ├── initia_names.py       # .init reverse lookup + 24h cache
│   ├── verifiers/
│   │   ├── __init__.py       # VERIFIERS registry by chain
│   │   └── cosmos_adr36.py   # Initia ADR-36 signArbitrary verify
│   └── deps.py               # get_current_user + require_session_key dependencies
│
├── vm/
│   ├── provider.py           # VM provider abstraction (Firecracker/Fly adapter)
│   ├── service.py            # provision / wake / drain / stop / snapshot
│   └── registry.py           # in-memory cache of user_vms state
│
├── proxy/
│   ├── middleware.py         # matches /api/v1/u/* → waker + forwarder
│   ├── forwarder.py          # mTLS httpx client with X-Hub-Secret
│   └── ws.py                 # WebSocket proxy (status/logs)
│
├── credits/
│   ├── service.py            # grant, debit, halt
│   ├── cron.py               # per-minute debit loop
│   └── router.py             # /credits, admin /credits/grant
│
├── market/
│   ├── pyth.py               # Pyth Hermes proxy
│   ├── twelvedata.py         # TwelveData client (rate-limited 8/min)
│   ├── cache.py              # read/write market_cache table
│   ├── scheduler.py          # APScheduler refresh
│   └── router.py             # /market/*
│
├── marketplace/
│   ├── models.py             # already in db/models, re-exported
│   ├── service.py            # publish, install, report, auto-delist
│   └── router.py             # /marketplace/*
│
├── indexer/
│   ├── mirror.py             # schema, write helpers
│   ├── pull.py               # cron — pull from user-servers
│   └── router.py             # /indexer/tx*
│
├── secrets/
│   ├── service.py            # AES-GCM encrypt/decrypt, KEK from env
│   ├── push.py               # push decrypted on wake to user-server
│   └── router.py             # /api/v1/secrets (write-only, never returns plaintext)
│
├── funder/
│   ├── wallet.py             # platform hot wallet management
│   └── cron.py               # 5h refill scan
│
├── ws/
│   ├── manager.py            # connection registry
│   └── router.py             # /ws/*
│
├── audit/
│   └── service.py            # append-only audit_log writes
│
├── otel/
│   └── exporter.py           # receives from user-server
│
├── admin/
│   └── router.py             # /admin/* (credits grant, marketplace delist, VM force-stop)
│
├── internal/
│   └── router.py             # user-server → hub callbacks (indexer flush, heartbeat)
│
└── utils/
    ├── mtls.py               # CA + cert mint
    └── errors.py             # shared error shape + exception mapping
```

## Key runtime behaviors

### Wake-proxy middleware
- Intercepts `/api/v1/u/*`
- Looks up `user_vms.status`
- If `stopped`: `vm/service.wake(user_id)` → blocks up to 10s → on success, updates `status=running`, `last_active_at=now()`
- Forwards original request via `proxy/forwarder` (mTLS)
- Propagates response body + status

### Credits debit cron
- Reads `user_vms` where `alive_agents > 0` (from heartbeat or cached status)
- Single transaction: debit + insert ledger row
- On `balance <= 0`: POST `/hub/halt` → user-server stops all agents; hub marks halt state; WS notify

### Scale-to-zero cron (every 5 min)
- Select VMs with `status='running' AND last_active_at < now()-5m AND alive_agents == 0`
- For each: POST `/hub/drain` → wait for ack → snapshot+stop via provider
- Update `status='stopped'`

### Indexer pull cron (every 30 min)
- For each `status='running'` VM: GET `/hub/indexer/since?ts=…`
- Bulk insert into `indexer_tx_mirror`
- Last-synced timestamp stored per-user on hub

### Funder cron (every 5 h)
- Iterate active VMs; top up each wallet to `FUND_FLOOR_WEI`
- Env configurable: `FUND_FLOOR_WEI`, `FUND_TOPUP_WEI`, `FUND_INTERVAL_SEC`, `FUND_MIN_RESERVE`

## What's reused from current hub

- `auth/` — JWT plumbing reused; register/login deleted; add nonce, verifiers, session keys, `.init`
- `market_cache/` — current implementation carries; move to `market/cache.py`
- `secrets/` — current AES layer reused
- `ws/` — extend to proxy WebSocket subscriptions through to user-server

## New modules

- `vm/` (entirely new)
- `proxy/` (entirely new — replaces current direct-agent proxy)
- `credits/` (entirely new)
- `funder/` (entirely new)
- `marketplace/` (entirely new)
- `indexer/` (entirely new mirror; current on-chain logger moves to user-server)
- `admin/` (entirely new)

## Removed from current hub

- `agent_manager.py` (moves to user-server `agents/service.py`)
- `docker/` orchestration (moves to user-server)
- agent proxy endpoints (become proxy middleware forwards)

## Config (env)

```
# Hub
DATABASE_URL=postgresql+asyncpg://…
JWT_SECRET=…
KEK=…                          # 32-byte base64
HUB_CA_KEY=…
INTERNAL_SECRET=…              # legacy name retained for user-server→hub auth

# Auth
AUTH_NONCE_TTL_SECONDS=300
AUTH_SESSION_TTL_SECONDS=28800
AUTH_MESSAGE_DOMAIN=artic.trade
AUTH_SUPPORTED_CHAINS=initia-testnet
INITIA_NAME_SERVICE_URL=…      # endpoint for .init reverse lookup

# VM provider
VM_PROVIDER=fly                # fly | firecracker
VM_PROVIDER_TOKEN=…
VM_IMAGE_TAG=user-server:v0.1.0

# Market
TWELVEDATA_API_KEY=…
PYTH_HERMES_URL=…

# Chain
HSK_RPC_URL=…
PLATFORM_WALLET_KEY=…
FUND_FLOOR_WEI=…
FUND_TOPUP_WEI=…
FUND_INTERVAL_SEC=18000

# OTel
OTEL_COLLECTOR_URL=…
```

## Health checks

- `/health` — liveness
- `/health/ready` — checks DB, VM provider API, market cache freshness

## Deployment

- Single container; scale vertically for alpha
- Postgres: managed service
- No load balancer in front at alpha (single instance); beta adds one + session affinity for WebSocket
