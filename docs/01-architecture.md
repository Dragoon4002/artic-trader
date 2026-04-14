# Architecture

## Overview

AI-powered quant trading engine. LLM selects strategies from 30+ algorithms, executes paper trades with dynamic risk management. Multi-agent system managed via terminal UI.

## System Topology

```
User
  |
  v
TUI (tui.py) — Textual terminal app
  |
  v
AgentManager (agent_manager.py) — subprocess orchestrator
  |  persists → ~/.arcgenesis/agents.json
  |
  +---> Agent 1 (uvicorn :8010) ---> TradingEngine
  +---> Agent 2 (uvicorn :8011) ---> TradingEngine
  +---> Agent N (uvicorn :801N) ---> TradingEngine
         |
         +-- Pyth (live prices, 27 symbols)
         +-- Twelve Data (OHLCV candles)
         +-- LLM (OpenAI/Anthropic/DeepSeek/Gemini)
         +-- MongoDB (optional cache)
         +-- CMC (metadata only — logo, description, supply)
```

## Entry Points

| Entry | Command | Purpose |
|-------|---------|---------|
| TUI | `python tui.py` | Primary interface — create/start/stop/monitor agents |
| Standalone API | `uvicorn app.main:app --port 8010` | Single engine (dev/debug) |

## Agent Lifecycle

```
CreateAgentScreen (TUI form)
    |
    v
manager.launch(symbol, amount_usdt, leverage, ...)
    |
    v
1. Assign port (8010+, first available)
2. subprocess.Popen(["python", "-m", "uvicorn", "app.main:app", "--port", N])
3. Poll /health for 15s
4. POST /start with trading config
5. Mark alive=True, save to agents.json
    |
    v
Trading loop running, TUI polls /status + /logs every 2s
```

**States:** stopped → starting → alive → stopping → stopped

## Per-Agent Process (FastAPI)

Each agent is an independent uvicorn process running `app.main:app`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Liveness check |
| `/start` | POST | Begin trading session (clears logs) |
| `/stop` | POST | Stop trading loop |
| `/status` | GET | Current state (price, position, PnL, strategy) |
| `/logs` | GET | Last 500 log entries |
| `/plan` | POST | AI strategy plan (no trading) |
| `/ai-planner` | POST | Full AI analysis |
| `/candles` | GET | OHLCV from Twelve Data |
| `/historical-data` | GET | Daily history from Twelve Data |
| `/token/{symbol}` | GET | Token metadata (CMC) + Pyth price |
| `/explore/crypto` | GET | Crypto market overview (Twelve Data) |
| `/explore/forex` | GET | Forex overview (Twelve Data) |

## Trading Loop (per tick)

```
engine.start() →
  1. Fetch initial price (Pyth)
  2. Fetch market summary
  3. LLM plans strategy (once)
  4. Pre-fetch candles (Twelve Data)
  5. Enter _trading_loop:
     while running:
       a. Fetch price (Pyth)
       b. Append to price_history (deque, 200 max)
       c. Check TP/SL → close if hit
       d. If supervisor_interval reached:
          - Fetch fresh candles
          - LLM supervisor check → KEEP/CLOSE/ADJUST_TP_SL
       e. Compute signal via selected quant algo
       f. Decide: OPEN_LONG, OPEN_SHORT, CLOSE, HOLD
       g. Execute (paper position)
       h. Log tick
       i. Sleep poll_seconds
```

## Data Sources

| Source | Data | Auth | Used For |
|--------|------|------|----------|
| **Pyth Hermes** | Live prices (27 cryptos) | None (public) | Engine tick loop, all price fetching |
| **Twelve Data** | OHLCV candles, historical, quotes | `TWELVE_DATA_API_KEY` | Strategy computation, charts |
| **CoinMarketCap** | Token metadata (logo, desc, supply) | `CMC_API_KEY` (optional) | `/token` endpoints only |
| **LLM** | Strategy planning, supervisor | Provider-specific key | Once at start + periodic supervisor |
| **MongoDB** | Cache for quotes, candles, Pyth | `MONGODB_URI` (optional) | Reduce API calls |

## File Map

```
bela-quant-engine/
├── tui.py                    # Terminal UI (Textual) — 5 screens
├── agent_manager.py          # Spawn/stop/poll uvicorn subprocesses
├── app/
│   ├── main.py               # FastAPI endpoints
│   ├── engine.py              # Trading loop + supervisor
│   ├── pyth_client.py         # Pyth Hermes price feeds (27 symbols)
│   ├── market.py              # MarketData (Pyth + Twelve Data)
│   ├── llm_planner.py         # Multi-LLM strategy planning
│   ├── market_analysis.py     # Feature engineering (ATR, ADX, vol)
│   ├── schemas.py             # Pydantic models
│   ├── paper.py               # Paper position tracking
│   ├── chat.py                # Multi-model copilot
│   ├── log_buffer.py          # In-memory log ring buffer
│   ├── cmc_client.py          # CMC metadata client
│   ├── db.py                  # MongoDB cache layer
│   ├── cache_refresh.py       # Background refresh (APScheduler)
│   ├── token_analysis.py      # LLM token deep-dives
│   ├── pancake_executor_stub.py # Blockchain stub (not implemented)
│   └── strategies/
│       ├── signals.py         # Strategy dispatcher
│       └── quant_algos/       # 30+ trading algorithms
│           ├── momentum_algos.py
│           ├── mean_reversion_algos.py
│           ├── volatility_algos.py
│           ├── volume_algos.py
│           ├── statistical_algos.py
│           ├── risk_sizing.py
│           └── time_filters.py
```

## Persistence

| Store | Location | Contents |
|-------|----------|----------|
| agents.json | `~/.arcgenesis/agents.json` | Agent configs (symbol, port, leverage, etc). Excludes API keys. |
| .env | project root | API keys (CMC, Twelve Data, LLM providers, MongoDB) |
| MongoDB | remote (optional) | Cached quotes, candles, Pyth prices |
| Log buffer | in-memory per agent | 2000 entries max, cleared on `/start` |
| Position | in-memory per agent | Paper position, lost on process death |

## Limitations

- **No central hub** — TUI is the only client, talks directly to agents
- **No Docker** — agents are bare subprocesses
- **Paper only** — blockchain execution is a stub
- **Single position** per agent — no portfolio management
- **No backtesting** — real-time only
- **No auth** — agent HTTP endpoints are unauthenticated
- **Logs volatile** — in-memory only, lost on restart
