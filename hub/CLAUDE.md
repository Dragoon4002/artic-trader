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
├── auth/                  # Authentication
│   ├── router.py          # /auth/login, /auth/refresh
│   ├── service.py         # JWT + API key verification
│   └── deps.py            # get_current_user dependency
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

- Agent CRUD, status proxy, log streaming (WebSocket)
- Auth (JWT + API key), secret management
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
