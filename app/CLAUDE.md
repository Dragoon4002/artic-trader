# App Module — Artic

Self-contained FastAPI trading engine. One instance = one symbol. Runs inside a Docker container managed by the hub.

## Folder Structure

```
app/
├── main.py              # FastAPI entry, route registration
├── engine.py            # Trading loop orchestration
├── schemas.py           # Pydantic models (shared types)
├── market/              # Market data clients
│   ├── pyth_client.py   # Pyth Hermes price feeds
│   ├── market.py        # TwelveData candle fetcher (via hub cache)
│   ├── market_analysis.py # Technical indicators (ATR, vol, ADX)
│   ├── cmc_client.py    # CoinMarketCap token metadata
│   ├── cache_refresh.py # Background cache refresh
│   └── token_analysis.py # LLM token analysis
├── llm/                 # LLM integration
│   ├── llm_planner.py   # Strategy selection + supervisor
│   └── chat.py          # Copilot chat interface
├── executor/            # Trade execution backends
│   ├── base.py          # BaseExecutor ABC
│   ├── paper.py         # Paper trading (in-memory)
│   └── hashkey.py       # HashKey Global REST API (TODO)
├── hub_callback.py      # Push status/trades/logs to hub (TODO)
├── log_buffer.py        # In-memory log ring buffer
└── strategies/          # See /app/strategies/CLAUDE.md
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Container health check |
| POST | /start | Start trading loop |
| POST | /stop | Stop trading loop |
| GET | /status | Current engine state + position |
| GET | /logs | Recent log entries |
| POST | /plan | Trigger LLM planning cycle |

## Called By

Hub only — clients never talk to app containers directly.

## Docs → `/docs/app/` (engine loop: `/docs/app/engine.md`)

## Conventions

- Log levels: init/llm/start/tick/action/sl_tp/stop/error/warn/supervisor
- Position state is in-memory, lost on restart — snapshots only persistence
- `live_mode` must be false unless HashKey executor is implemented
