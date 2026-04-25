# Hub Module — Artic

Central FastAPI orchestrator. Owns user auth, VM lifecycle (Morph), secrets management,
market cache, and the client-facing REST/WebSocket API. Proxies all user-server calls
via wake-proxy middleware (`/api/v1/u/*`).

## Folder Structure

```
hub/
├── server.py              # FastAPI entry, route registration, lifespan
├── config.py              # Settings (env-based)
├── auth/                  # Wallet-connect authentication (Initia/Cosmos ADR-36)
│   ├── router.py          # /auth/nonce, /auth/verify, /auth/refresh, /auth/me, /auth/session
│   ├── service.py         # JWT, nonce, sign-in message
│   ├── session.py         # session-key issue/verify/revoke + monotonic-nonce guard
│   ├── initia_names.py    # .init username reverse lookup + 24h cache
│   ├── verifiers/         # Chain-pluggable sig verifiers (cosmos_adr36.py)
│   └── deps.py            # get_current_user + require_session_key
├── vm/                    # Morph VM lifecycle
│   ├── service.py         # provision, wake, drain, stop, touch
│   ├── provider.py        # Morph API client (start/stop/snapshot)
│   ├── morph_provider.py  # Morph-specific impl
│   └── registry.py        # In-memory VM state cache
├── proxy/                 # Wake-proxy middleware + WS stub
│   ├── middleware.py      # Intercepts /api/v1/u/* — wakes VM, forwards to user-server
│   ├── forwarder.py       # httpx async forwarder (path rewrite: /api/v1/u/<x> → /<x>)
│   └── ws.py              # WebSocket proxy stubs (/ws/u/agents/*/logs|status)
├── internal/              # Hub-internal push endpoints (from agents via user-server)
│   └── router.py          # /internal/agents/{id}/status, /trades, /logs
├── ws/                    # WebSocket streaming to dashboard
│   ├── manager.py         # Connection pool
│   └── broadcaster.py     # Poll agents, push to WS clients
├── market_cache/          # Centralized candle cache (60s refresh)
│   └── service.py
├── secrets/               # Encrypted secret management
│   └── service.py
├── images/                # Serve agent/user-server Docker image tarballs to VMs
│   └── router.py          # GET /internal/v1/images/<file>
├── db/                    # SQLAlchemy async (PostgreSQL)
│   ├── base.py
│   └── models/            # users, user_vms, user_secrets, agents, trades, log_entries...
└── alembic/               # DB migrations
```

## Exposes To Clients

- `/api/v1/u/*` — proxied to user-server (wake-proxy, JWT auth)
- `/auth/*` — Initia wallet auth (ADR-36 sig → JWT + session key)
- `/api/market/candles` — cached candle data
- `/ws/u/agents/*/logs` — WebSocket log streaming (stub, pending impl)

## Wake-Proxy Flow

1. Request hits `/api/v1/u/<path>`
2. Middleware resolves user_id from JWT or API key
3. Looks up VM in registry; if stopped → calls `vm_service.wake()`
4. Forwards to `vm_endpoint/<path>` via `Forwarder` (strips auth headers, adds `X-Hub-Secret`)
5. On success, touches `last_active_at`

## Docs

- Auth: `/docs/connections/auth-flow.md`
- Service map: `/docs/connections/service-map.md`
- On-chain: `/docs/connections/onchain.md`
- Data model: `/docs/architecture/data-model.md`
