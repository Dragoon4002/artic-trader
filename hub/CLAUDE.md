# Hub Module — Artic

Standalone FastAPI server. Owns agent lifecycle, user auth, secrets, market cache, and client-facing REST/WebSocket API.

## Folder Structure

```
hub/
├── server.py              # FastAPI entry, route registration
├── config.py              # Settings (env-based)
├── agents/                # Agent lifecycle
│   ├── router.py          # /api/agents/* endpoints
│   ├── service.py         # Agent spawn/stop logic
│   └── registry.py        # In-memory live state cache
├── docker/                # Container management
│   ├── manager.py         # Docker SDK create/start/stop/remove
│   └── ports.py           # Atomic thread-safe port allocation
├── auth/                  # Wallet-connect authentication
│   ├── router.py          # /auth/nonce, /auth/verify, /auth/refresh, /auth/me, /auth/session
│   ├── service.py         # JWT, nonce, canonical sign-in message
│   ├── session.py         # session-key issue/verify/revoke + monotonic-nonce guard
│   ├── initia_names.py    # .init reverse lookup + 24h cache
│   ├── verifiers/         # chain-pluggable sig verifiers (cosmos_adr36.py for Initia)
│   └── deps.py            # get_current_user + require_session_key
├── internal/              # Agent→Hub push endpoints
│   └── router.py          # /internal/agents/{id}/status, /trades, /logs
├── ws/                    # WebSocket streaming
│   ├── manager.py         # Connection pool
│   └── broadcaster.py     # Poll agents, push to WS clients
├── market_cache/          # Centralized candle cache
│   └── service.py         # APScheduler refresh, 60s staleness
├── secrets/               # Secret management
│   └── service.py         # Encrypted DB + ephemeral override
├── db/                    # Database layer
│   ├── base.py            # SQLAlchemy async engine, get_session
│   └── models/            # ORM models (one per table)
├── client.py              # Hub SDK (used by all clients)
└── alembic/               # DB migrations
```

## Exposes To Clients

- Agent CRUD, status proxy, log streaming (WebSocket). State-changing endpoints require session-key headers (`X-Session-Id`, `X-Session-Nonce`, `X-Session-Sig`).
- Auth: wallet-signature (Initia/Cosmos ADR-36) → JWT + session key; `.init` username resolved at login
- Market candle cache (`GET /api/market/candles`)

## Receives From Agents (push-based)

| Internal Endpoint | Auth | Purpose |
|-------------------|------|---------|
| POST /internal/agents/{id}/status | X-Internal-Secret | Status push every tick |
| POST /internal/trades | X-Internal-Secret | Trade open/close events |
| POST /internal/logs | X-Internal-Secret | Log batch every 10 ticks |

## Docs

- Auth: `/docs/connections/auth-flow.md`
- Service map: `/docs/connections/service-map.md`
- Data model: `/docs/architecture/data-model.md`
