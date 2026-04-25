# Current Flow — Artic

Snapshot of what runs end-to-end **today**. Flags stubs, missing pieces, and divergences from aspirational docs.

> For contracts, schema, and protocol specs see [architecture/overview.md](architecture/overview.md), [architecture/data-model.md](architecture/data-model.md), [connections/service-map.md](connections/service-map.md).

## Boot sequence

1. `docker-compose up` — hub + Postgres on `artic-net` bridge
2. `./scripts/build-app-image.sh` — builds `artic-app:latest` for agent containers
3. Hub `server.py` startup runs `init_db()` (create_all — **Alembic dir empty**) + APScheduler candle refresh (60s)
4. Client (TUI/CLI/Telegram) → `POST /auth/login` → JWT in memory / `~/.artic/token`

## Agent create → start

```
client → POST /api/agents              (JWT)
      ↳ hub persists row (status=stopped)

client → POST /api/agents/{id}/start
      ↳ hub/agents/service.spawn_agent()
        ├── allocate port (atomic lock, hub/docker/ports.py)
        ├── resolve secrets: agent_overrides → user_secrets → .env
        ├── docker.run(artic-app, network=artic-net, env={HUB_URL, HUB_AGENT_ID, INTERNAL_SECRET, API_KEYS, ...})
        ├── poll GET artic-agent-{id}:8000/health (500ms, 20s timeout)
        └── POST artic-agent-{id}:8000/start {StartRequest}
      ↳ DB: status=alive, container_id, port
```

## Tick loop (inside container)

`app/engine.py::_trading_loop` every `poll_seconds`:

1. Pyth Hermes live price → append `price_history` (deque 200)
2. If in position: TP/SL check → close if hit → `hub_callback.report_trade()`
3. If `supervisor_interval` reached: fetch fresh candles from `hub /api/market/candles` → LLM supervisor (KEEP/CLOSE/ADJUST)
4. Session drawdown check → stop if exceeded
5. Compute signal via selected quant algo (`app/strategies/signals.py`)
6. Decide OPEN_LONG / OPEN_SHORT / CLOSE / HOLD
7. Execute via `PaperExecutor` (**HashKeyExecutor is skeleton — no live API calls yet**)
8. `hub_callback.report_status()` every tick
9. Batched logs → `hub_callback.flush_logs()` every 10 ticks
10. Supervisor decisions → `onchain_logger.log_decision()` if HSK_RPC_URL set

## Push path (agent → hub)

| Call | Endpoint | Frequency |
|------|----------|-----------|
| status | POST /internal/agents/{id}/status | every tick |
| trade | POST /internal/trades | on open/close |
| logs | POST /internal/logs | every 10 ticks (batched) |
| onchain decision | POST /internal/onchain-decisions | on supervisor tx confirm |
| onchain trade | POST /internal/onchain-trades | on trade tx confirm |

All carry `X-Internal-Secret` header (matches `INTERNAL_SECRET` env on hub).

Hub `internal/router.py` upserts registry + bulk-inserts DB + broadcasts to WS subscribers.

## Stream path (hub → client)

- `WS /ws/agents/{id}/status` — status ticks pushed to all subscribers
- `WS /ws/agents/{id}/logs` — log entries pushed on arrival
- `WS /ws/prices` — Pyth price broadcast

## On-chain (HashKey Chain)

- Contracts deployed: `DecisionLogger.sol`, `TradeLogger.sol` (addresses + ABI in `contracts/*_deployed.json`)
- `app/onchain_logger.py` + `app/onchain_trade_logger.py` — Web3, HMAC signing, real tx send
- Enabled iff `HSK_RPC_URL` + `HSK_PRIVATE_KEY` + deployed.json present
- Full reasoning text stored off-chain in `onchain_decisions` table — only `session_id` hash + tx_hash on-chain

## What's real vs stubbed

| Area | State |
|------|-------|
| Hub auth (JWT + API key) | real |
| Agent CRUD + Docker spawn | real |
| Internal push endpoints | real |
| Market cache (TwelveData + scheduler) | real |
| Pyth price proxy + WS broadcast | real |
| Secrets (encrypted DB) | real |
| Paper executor | real (fixed + dynamic TP/SL) |
| On-chain loggers | real (web3 calls) |
| TUI / CLI / Telegram | real (all SDK-backed) |
| LLM planner + supervisor | real (OpenAI / Anthropic / DeepSeek / Gemini) |
| **HashKey live executor** | **skeleton** — ABC methods, HMAC sign, no real REST calls |
| **Alembic migrations** | **empty** — `create_all()` only (dev) |
| **Web dashboard** | **not a dashboard** — landing + docs MDX only |
| **Tests** | **near zero** — 1 TS file (pyth fetch), no hub/app unit tests |

## Client summary

| Client | Path | Transport | State |
|--------|------|-----------|-------|
| TUI | `/clients/tui/` | HubClient SDK (`hub/client.py`) | full screens, hub-backed |
| CLI | `/clients/cli/` | HubClient SDK | full command set, token at `~/.artic/token` |
| Telegram | `/clients/telegram/` | HubClient SDK | commands wired, push alerts |
| Web | `/clients/web/` | Next.js 15, static | marketing + MDX docs only |

## Known gaps (ordered by impact)

1. HashKey live executor not wired — `live_mode=true` will fail
2. No Alembic migrations — schema changes require drop+recreate
3. Zero hub/app unit tests — regressions uncaught
4. No web dashboard — agent control requires TUI/CLI/Telegram
5. `.claude/plans/` referenced by history is absent (pointer removed)
