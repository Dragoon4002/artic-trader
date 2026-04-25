# App Module — Artic

Self-contained FastAPI trading engine. One instance = one symbol. Runs inside a Docker
container managed by user-server on a Morph VM. Pushes status/trades/logs to user-server
every tick. Logs AI decisions and trades to Initia MiniEVM on-chain.

## Folder Structure

```
app/
├── main.py                  # FastAPI entry, route registration
├── engine.py                # Trading loop orchestration
├── schemas.py               # Pydantic models (shared types)
├── hub_callback.py          # Push status/trades/logs to user-server
├── log_buffer.py            # In-memory log ring buffer (flushed every 10 ticks)
├── onchain_logger.py        # DecisionLogger contract client (supervisor decisions)
├── onchain_trade_logger.py  # TradeLogger contract client (trade open/close)
├── market/                  # Market data
│   ├── pyth_client.py       # Pyth Hermes price feeds
│   ├── market.py            # TwelveData candle fetcher
│   ├── market_analysis.py   # Technical indicators (ATR, vol, ADX)
│   ├── cmc_client.py        # CoinMarketCap token metadata
│   └── price_listener.py    # Hub WS price feed listener
├── llm/                     # LLM integration
│   ├── llm_planner.py       # Strategy selection + supervisor check
│   └── chat.py              # Copilot chat interface
├── executor/                # Trade execution backends
│   ├── paper.py             # Paper trading (in-memory, default)
│   └── hashkey.py           # HashKey Global REST (live, optional)
└── strategies/              # See /app/strategies/CLAUDE.md
```

## Endpoints (called by user-server only)

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Container health check |
| POST | /start | Start trading loop |
| POST | /stop | Stop trading loop |
| GET | /status | Engine state + position + active_strategy |
| GET | /logs | Recent log entries |
| POST | /plan | Trigger LLM planning cycle |

## Env Vars (injected by spawner)

| Var | Purpose |
|-----|---------|
| `HUB_AGENT_ID` | Agent UUID |
| `SYMBOL` | Trading symbol |
| `HUB_URL` | User-server base URL (for callbacks) |
| `INTERNAL_SECRET` | Auth for user-server push endpoints |
| `STRATEGY_POOL` | JSON list of allowed strategy names |
| `LLM_PROVIDER` / `LLM_MODEL` | LLM selection |
| `RISK_PARAMS` | JSON risk config |
| `CHAIN_RPC_URL` | Initia MiniEVM JSON-RPC (on-chain logging) |
| `CHAIN_PRIVATE_KEY` | Platform wallet private key (on-chain logging) |

## On-Chain Logging

Every supervisor decision → `onchain_logger.py` → `DecisionLogger` contract
Every trade open/close → `onchain_trade_logger.py` → `TradeLogger` contract
Gracefully disabled if `CHAIN_RPC_URL` or `CHAIN_PRIVATE_KEY` absent.
Full spec: `/docs/connections/onchain.md`

## Conventions

- Log levels: init/llm/start/tick/action/sl_tp/stop/error/warn/supervisor
- Position state is in-memory only — lost on container restart
- `live_mode=false` by default (paper trading); set true for HashKey execution
- `HUB_URL` must point to user-server (`http://localhost:8000` on the VM)
