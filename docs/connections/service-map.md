# Service Map — Artic

> **Source of truth for service boundaries.** Update this file **before** adding any new call path.

## Call Graph

| Caller | Callee | Protocol | Direction | Notes |
|--------|--------|----------|-----------|-------|
| clients/* | hub | REST + WebSocket | → | All client→system comms through hub |
| hub | app containers | HTTP | → | /health, /start, /stop at spawn time |
| app containers | hub /internal/* | HTTP | ← push | Status, trades, logs (X-Internal-Secret) |
| app containers | hub /api/market/candles | HTTP | → | Cached candle data from hub |
| app | Pyth Hermes | REST | → | Live prices, no auth, no rate limit |
| hub | TwelveData | REST | → | Candle refresh, **rate-limited 8 req/min** |
| app | LLM provider | REST | → | Strategy selection + risk analysis |
| hub | PostgreSQL | SQL | → | All persistent state |
| app | HashKey Chain | RPC | → | DecisionLogged events (on-chain) |

## Port Map

| Service | Default Port | Notes |
|---------|-------------|-------|
| Hub | 9000 | Client-facing API + WebSocket |
| Agent containers | 8000 (internal) | Docker internal DNS: `artic-agent-{id}:8000` |
| Pyth Hermes | — | hermes.pyth.network (public) |
| TwelveData | — | api.twelvedata.com (API key required) |

## Internal Endpoints (agent → hub, push-based)

| Endpoint | Auth | Frequency |
|----------|------|-----------|
| POST /internal/agents/{id}/status | X-Internal-Secret | Every tick |
| POST /internal/trades | X-Internal-Secret | On position open/close |
| POST /internal/logs | X-Internal-Secret | Every 10 ticks (batch) |

## Rules

- Clients **never** call app containers directly
- Hub is the only service that writes to PostgreSQL
- Agents fetch candles from hub cache — never call TwelveData directly
- TwelveData rate budget managed centrally by hub APScheduler
- Port allocation uses atomic thread-safe lock (`hub/docker/ports.py`)
