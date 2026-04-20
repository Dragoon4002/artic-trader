# Hub Module — Artic (alpha Phase 1)

Persistent FastAPI server. Owns auth, wake-proxy routing, cross-user state, market cache, secrets, observability. Per-user agent/strategy execution lives on the user-server (reached via the proxy).

## Folder Structure

```
hub/
├── server.py          # FastAPI app factory, lifespan, middleware registration
├── config.py          # pydantic-settings (env-based)
├── auth/              # JWT + bcrypt + rotating refresh tokens
├── secrets/           # AES-GCM storage + wake-time push
├── vm/                # Provider Protocol, MorphProvider, VMService, registry
├── proxy/             # Wake-proxy middleware + mTLS forwarder + /ws/u/*
├── market/            # Pyth live prices + TwelveData candle cache + scheduler
├── internal/          # User-server → hub callbacks (heartbeat/flush/otel stubs)
├── audit/             # Append-only audit_log writer
├── utils/             # mtls.py (CA + per-VM cert), errors.py (error envelope)
├── db/                # SQLAlchemy async + models + Alembic
├── ws/                # Price-broadcast WebSocket manager
├── deprecated/        # agents/, docker/, agent_manager.py — pending move to user-server
├── credits/ funder/ marketplace/ indexer/ admin/ otel/   # Phase 4/5 stubs
└── alembic/           # Migrations
```

## Current endpoints

- `POST /auth/{register,login,refresh,logout}`, `GET /auth/me`, `POST /api/keys`
- `POST /api/v1/secrets`, `GET /api/v1/secrets`, `DELETE /api/v1/secrets/{key}`
- `GET /api/market/{price/{sym},prices,candles}`
- `/api/v1/u/*` (proxied to user-server; cold-wakes VM)
- `POST /internal/v1/{credits/heartbeat,indexer/flush,otel/spans}` (stubs)
- `GET /health`, `GET /health/ready`
- `/ws/u/agents/{id}/{status,logs}` (stubbed — full impl lands with user-server)
- `/ws/prices` (live price broadcast)

## Docs

- Target architecture: `/docs/alpha/plans/hub.md`
- VM provider contract: `/docs/alpha/morph-vm.md`
- Data model: `/docs/alpha/data-model.md`
- Security: `/docs/alpha/security-model.md`
