# Artic — System Architecture

## Overview

Artic is an AI-powered multi-agent trading orchestration platform. A central hub server manages all agent lifecycle, authentication, market data caching, and client connections. Isolated agent containers run the trading engine — fetching prices, running quantitative strategies, and delegating strategy selection to an LLM. Users access the system through any of four client interfaces: TUI, CLI, Telegram bot, or web dashboard, all speaking the same hub API.

---

## Repository Structure

```
artic/
├── artic-hub/          # Central server — orchestration, auth, DB, API gateway
├── artic-app/          # Agent engine — trading loop, strategies, LLM, market data
└── artic-client/       # All user-facing interfaces + shared SDK
```

The database lives inside `artic-hub`. There is no separate DB repo — PostgreSQL is a dependency of the hub, managed via Docker Compose.

---

## System Topology

```
                        ┌─────────────────────────────────────┐
                        │            artic-hub                 │
                        │                                      │
  ┌─────────────────┐   │  ┌──────────────┐  ┌─────────────┐ │
  │  artic-client   │   │  │  FastAPI     │  │ PostgreSQL  │ │
  │                 │   │  │  server.py   │  │             │ │
  │  TUI (Textual)  │◄──┼─►│  auth/       │  │ agents      │ │
  │  CLI (Typer)    │   │  │  agents/     │  │ trades      │ │
  │  Telegram bot   │   │  │  ws/         │  │ log_entries │ │
  │  Web (React)    │   │  │  market_     │  │ users       │ │
  │                 │   │  │  cache/      │  │ market_     │ │
  │  [hub_sdk/]     │   │  │              │  │ cache       │ │
  └─────────────────┘   │  └──────┬───────┘  └─────────────┘ │
                        │         │                            │
                        └─────────┼────────────────────────────┘
                                  │ Docker SDK
                                  │ spawn / stop / poll
                                  ▼
               ┌──────────────────────────────────────┐
               │         Docker bridge: artic-net      │
               │                                      │
               │  ┌─────────────┐  ┌─────────────┐   │
               │  │ artic-app   │  │ artic-app   │   │
               │  │ container 1 │  │ container 2 │   │
               │  │ BTCUSDT     │  │ ETHUSDT     │   │
               │  │ :8000       │  │ :8000       │   │
               │  └──────┬──────┘  └──────┬──────┘   │
               └─────────┼────────────────┼───────────┘
                         │                │
         ┌───────────────┼────────────────┘
         ▼               ▼
  External data sources (per agent):
  - Pyth Hermes        (live prices, no key)
  - Twelve Data        (OHLCV candles, via hub cache)
  - CoinMarketCap      (token metadata, optional)
  - OpenAI / Anthropic / DeepSeek / Gemini   (LLM)
  - HashKey Global     (live executor, REST API)
```

---

## Repo 1: `artic-hub`

The single source of authority. Runs as a standalone long-lived server. All clients connect here. All agents are spawned from here. No client ever talks to an agent directly.

### Responsibilities

- User authentication (JWT + API key)
- Agent CRUD — create, start, stop, delete, list
- Spawning and managing agent Docker containers
- Proxying status and log requests to alive agents
- Persisting all agent configs, trade records, and log entries to PostgreSQL
- Providing a shared, rate-limit-aware market data cache
- Streaming logs and status updates to clients via WebSocket
- Exposing an internal API for agents to POST state changes back to the hub

### File Structure

```
artic-hub/
├── main.py                        # FastAPI app factory, router registration, CORS, lifespan
├── config.py                      # Pydantic Settings — reads all env vars
├── docker-compose.yml             # Hub + PostgreSQL + (optional) Redis
│
├── auth/
│   ├── models.py                  # User ORM model, APIKey ORM model
│   ├── schemas.py                 # LoginRequest, RegisterRequest, TokenResponse
│   ├── service.py                 # JWT issue/verify, bcrypt password hash, API key generation
│   ├── router.py                  # POST /auth/register, /auth/login, /auth/refresh
│   └── dependencies.py            # FastAPI Depends: get_current_user (JWT or API key)
│
├── agents/
│   ├── models.py                  # AgentConfig ORM model (maps to agents table)
│   ├── schemas.py                 # AgentCreateRequest, AgentInfo, AgentListResponse
│   ├── registry.py                # In-memory live state — port map, container ID, PID, alive flag
│   ├── service.py                 # Business logic: create, launch, stop, delete, get_status
│   └── router.py                  # /api/agents CRUD + proxy endpoints
│
├── docker/
│   ├── manager.py                 # Docker SDK wrapper — run, stop, remove, inspect containers
│   ├── health.py                  # Poll agent /health until ready or timeout (20s, 500ms interval)
│   └── ports.py                   # Atomic port allocator — thread-safe, no race condition
│
├── ws/
│   ├── manager.py                 # WebSocket connection registry, keyed by agent_id
│   ├── router.py                  # WS /ws/agents/{id}/logs, WS /ws/agents/{id}/status
│   └── broadcaster.py             # Background task: polls alive agents, pushes to WS clients
│
├── db/
│   ├── base.py                    # SQLAlchemy async engine, session factory
│   ├── init_db.py                 # Create all tables on startup
│   └── migrations/                # Alembic migration files
│       ├── env.py
│       └── versions/
│
├── models/
│   ├── agent.py                   # agents table ORM
│   ├── trade.py                   # trades table ORM
│   ├── log_entry.py               # log_entries table ORM
│   └── user.py                    # users table ORM
│
├── market_cache/
│   ├── models.py                  # market_cache table ORM
│   ├── service.py                 # get_candles, set_candles, get_price — DB-backed
│   ├── scheduler.py               # APScheduler jobs — background candle refresh per symbol
│   └── router.py                  # GET /api/market/candles, GET /api/market/price/{symbol}
│
├── internal/
│   └── router.py                  # POST /internal/agents/{id}/status (agent → hub callbacks)
│                                  # POST /internal/trades (agent → hub trade records)
│                                  # POST /internal/logs  (agent → hub log entries)
│
└── requirements.txt
```

### Hub API Surface

```
# Authentication
POST   /auth/register                      Register new user
POST   /auth/login                         Get JWT token
POST   /auth/refresh                       Refresh JWT

# Agent management (JWT or API key required)
POST   /api/agents                         Create agent (store config in DB)
GET    /api/agents                         List agents (user-scoped)
GET    /api/agents/{id}                    Get agent detail
POST   /api/agents/{id}/start              Spawn Docker container, POST /start to agent
POST   /api/agents/{id}/stop              POST /stop to agent, then stop container
DELETE /api/agents/{id}                    Remove agent record and container
GET    /api/agents/{id}/status             Proxy GET /status from alive agent
GET    /api/agents/{id}/logs              Read log_entries from DB (survives restarts)
GET    /api/agents/{id}/metrics            Sharpe ratio, win rate, max drawdown from trades table
POST   /api/agents/kill-all               Stop all alive agents atomically (emergency)

# Market data (shared cache, rate-limit aware)
GET    /api/market/candles                Cached OHLCV — params: symbol, interval
GET    /api/market/price/{symbol}         Live price from Pyth Hermes

# WebSocket streams
WS     /ws/agents/{id}/logs               Stream log entries in real time
WS     /ws/agents/{id}/status             Stream status ticks in real time

# Internal (agent → hub, not exposed to clients)
POST   /internal/agents/{id}/status       Agent pushes status every tick
POST   /internal/trades                   Agent pushes completed trade record
POST   /internal/logs                     Agent pushes log batch

# Health
GET    /api/health
```

### Database Schema

**users**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | TEXT UNIQUE | |
| hashed_password | TEXT | bcrypt |
| api_key | TEXT UNIQUE | SHA-256 hash of raw key |
| created_at | TIMESTAMP | |

**agents**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK → users | |
| name | TEXT | |
| symbol | TEXT | e.g. BTCUSDT |
| amount_usdt | FLOAT | |
| leverage | INT | 1–10 (HashKey limit) |
| risk_profile | TEXT | conservative / moderate / aggressive |
| timeframe | TEXT | 1m / 5m / 15m / 30m / 1h / 4h / 1d |
| poll_seconds | FLOAT | tick interval |
| tp_pct | FLOAT | take-profit % |
| sl_pct | FLOAT | stop-loss % |
| tp_sl_mode | TEXT | fixed / dynamic |
| supervisor_interval | FLOAT | seconds between LLM rechecks |
| llm_provider | TEXT | openai / anthropic / deepseek / gemini |
| live_mode | BOOL | false = paper, true = HashKey live |
| max_session_loss_pct | FLOAT | session drawdown limit |
| status | TEXT | stopped / starting / alive / stopping / error |
| port | INT | host port mapped to container :8000 |
| container_id | TEXT | Docker container ID |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

**trades**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| agent_id | UUID FK → agents | |
| side | TEXT | LONG / SHORT |
| entry_price | FLOAT | |
| exit_price | FLOAT | null if still open |
| size_usdt | FLOAT | |
| leverage | INT | |
| pnl_usdt | FLOAT | null if still open |
| strategy | TEXT | e.g. ema_crossover |
| open_at | TIMESTAMP | |
| close_at | TIMESTAMP | null if still open |
| close_reason | TEXT | TP / SL / SUPERVISOR / MANUAL |
| tx_hash | TEXT | null for paper trades |

**log_entries**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| agent_id | UUID FK → agents | |
| ts | TIMESTAMP | |
| level | TEXT | init / llm / tick / action / sl_tp / supervisor / error / warn |
| message | TEXT | |

**market_cache**
| Column | Type | Notes |
|--------|------|-------|
| symbol | TEXT PK (composite) | |
| timeframe | TEXT PK (composite) | |
| candles | JSONB | array of OHLCV objects |
| fetched_at | TIMESTAMP | |

---

## Repo 2: `artic-app`

The trading engine. Runs as a stateless FastAPI process inside a Docker container. Receives all config via environment variables from the hub on spawn. Reports every meaningful state change back to the hub via POST calls — so the hub's DB is always the system of record, and the agent can crash and restart without data loss.

### Responsibilities

- Running the tick-by-tick trading loop
- Fetching live prices from Pyth Hermes
- Fetching OHLCV candles from hub cache (falls back to Twelve Data directly if hub URL not set)
- Delegating strategy selection to the LLM (once at start, then on each supervisor interval)
- Computing signals from 30+ quantitative algorithms
- Executing paper trades (PaperExecutor) or live trades (HashKeyExecutor)
- POSTing all state changes to hub's internal API

### File Structure

```
artic-app/
├── main.py                        # FastAPI app — all endpoints unchanged from current
├── engine.py                      # Trading loop — modified to POST state to hub
├── config.py                      # Reads env vars: HUB_URL, HUB_AGENT_ID, all API keys
├── schemas.py                     # All Pydantic models — unchanged + HubConfig schema
│
├── market/
│   ├── pyth_client.py             # Pyth Hermes live price feeds (27 symbols, dynamic lookup)
│   ├── market.py                  # MarketData — candles via hub cache or direct Twelve Data
│   ├── market_analysis.py         # Feature engineering: ATR, ADX, vol regime, spread
│   └── cmc_client.py              # CoinMarketCap metadata (token logo, description, supply)
│
├── llm/
│   ├── llm_planner.py             # Multi-provider strategy planner (OpenAI / Anthropic / DeepSeek / Gemini)
│   ├── token_analysis.py          # LLM deep-dive on individual tokens
│   └── chat.py                    # Multi-model copilot endpoint
│
├── executor/
│   ├── base.py                    # BaseExecutor ABC
│   ├── paper.py                   # PaperExecutor — in-memory position, reports to hub
│   └── hashkey.py                 # HashKeyExecutor — HashKey Global REST API (live trading)
│
├── strategies/
│   ├── signals.py                 # Strategy dispatcher — maps name → function
│   └── quant_algos/
│       ├── momentum_algos.py      # 8 momentum strategies
│       ├── mean_reversion_algos.py # 6 mean reversion strategies
│       ├── volatility_algos.py    # 3 volatility strategies
│       ├── volume_algos.py        # 3 volume strategies (funding rate now live via HashKey)
│       ├── statistical_algos.py   # 2 statistical strategies
│       ├── risk_sizing.py         # Position sizing helpers
│       └── time_filters.py        # Session/time-based filters
│
├── db.py                          # MongoDB optional cache layer (unchanged)
├── cache_refresh.py               # Background candle refresh (unchanged)
├── log_buffer.py                  # In-memory log ring buffer (2000 entries)
│
├── Dockerfile
└── requirements.txt
```

### Agent Endpoints (unchanged)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Liveness check — hub polls this on startup |
| `/start` | POST | Begin trading session with StartRequest config |
| `/stop` | POST | Stop trading loop gracefully |
| `/status` | GET | Current state: price, position, PnL, strategy |
| `/logs` | GET | Last N log entries from ring buffer |
| `/plan` | POST | AI strategy plan (no trading) |
| `/ai-planner` | POST | Full AI market analysis |
| `/candles` | GET | OHLCV from cache or Twelve Data |
| `/historical-data` | GET | Daily history from Twelve Data |
| `/token/{symbol}` | GET | Token metadata (CMC) + Pyth price |
| `/explore/crypto` | GET | Crypto market overview |
| `/explore/forex` | GET | Forex overview |

### Trading Loop

```
engine.start()
  1. Read config from env vars
  2. Fetch initial price (Pyth)
  3. Fetch market regime summary (ATR, ADX, vol)
  4. LLM selects strategy → POST strategy to hub /internal/agents/{id}/status
  5. Pre-fetch candles from hub cache
  6. Enter _trading_loop:

     while running:
       a. Fetch price (Pyth)
       b. Append to price_history (deque, 200 max)
       c. Check TP/SL → close if hit
          → POST trade to hub /internal/trades
       d. If supervisor_interval reached:
          - Fetch fresh candles from hub cache
          - LLM supervisor check → KEEP / CLOSE / ADJUST_TP_SL
       e. Check session drawdown limit → stop if exceeded
       f. Compute signal via selected quant algo
       g. Decide: OPEN_LONG / OPEN_SHORT / CLOSE / HOLD
       h. Execute via selected executor (paper or HashKey)
       i. POST status tick to hub /internal/agents/{id}/status
       j. Batch log entries → POST to hub /internal/logs every 10 ticks
       k. Sleep poll_seconds
```

### Executor Interface

```python
class BaseExecutor(ABC):
    async def open_long(self, symbol: str, size_usdt: float, price: float) -> dict: ...
    async def open_short(self, symbol: str, size_usdt: float, price: float) -> dict: ...
    async def close_position(self, symbol: str, side: str) -> dict: ...
    async def get_position(self, symbol: str) -> dict | None: ...
    async def get_balance(self) -> float: ...
    async def set_leverage(self, symbol: str, leverage: int) -> None: ...
    async def get_funding_rate(self, symbol: str) -> float: ...  # live in HashKeyExecutor
```

### HashKey Executor Mapping

| BaseExecutor method | HashKey Global API endpoint |
|--------------------|-----------------------------|
| `open_long` | `POST /api/v1/futures/order` side=BUY |
| `open_short` | `POST /api/v1/futures/order` side=SELL |
| `close_position` | `POST /api/v1/futures/order` reduceOnly=true |
| `get_position` | `GET /api/v1/futures/position` |
| `get_balance` | `GET /api/v1/futures/account/balance` |
| `set_leverage` | `POST /api/v1/futures/leverage` |
| `get_funding_rate` | `GET /api/v1/futures/fundingRate` |

HashKey perpetuals support 1–10x leverage, 12 pairs (BTC, ETH, and others), USDT-margined, 24/7.

---

## Repo 3: `artic-client`

All user-facing interfaces. Every client uses the `hub_sdk` package — no client ever imports agent code or talks directly to a container. The SDK is the only dependency on the hub's API contract.

### File Structure

```
artic-client/
│
├── hub_sdk/
│   ├── client.py                  # HubClient — all HTTP and WebSocket methods
│   ├── models.py                  # Shared Pydantic models (AgentInfo, StatusResponse, etc.)
│   ├── exceptions.py              # HubError, AuthError, AgentNotFound, RateLimitError
│   └── auth.py                    # Token storage, refresh logic, config file R/W
│
├── tui/
│   ├── app.py                     # Textual TUI app — refactored to use HubClient
│   └── screens/
│       ├── dashboard.py           # Master-detail agent list + live status panel
│       ├── create_agent.py        # Agent creation form wizard
│       ├── log_viewer.py          # Live log stream via WebSocket
│       └── theme.py               # 5 themes: hacker-green, cyber-finance, neon, midnight, vapor
│
├── cli/
│   ├── main.py                    # Typer app entrypoint
│   └── commands/
│       ├── agents.py              # artic agents list | create | start | stop | delete
│       ├── logs.py                # artic logs {id} [--follow]
│       ├── status.py              # artic status {id}
│       ├── market.py              # artic market price {symbol} | candles {symbol}
│       └── auth.py                # artic login | logout | whoami
│
├── telegram/
│   ├── bot.py                     # python-telegram-bot entrypoint (webhook or polling)
│   └── handlers/
│       ├── auth.py                # /connect <api_key> — link Telegram to Artic account
│       ├── agents.py              # /agents, /launch wizard, /stop, /kill
│       ├── status.py              # /status <name>, /pnl
│       ├── logs.py                # /logs <name>
│       └── alerts.py              # Push: drawdown, TP/SL, crash, rebalance
│
└── web/
    ├── src/
    │   ├── App.tsx
    │   ├── api/
    │   │   ├── client.ts          # Typed fetch wrapper around hub endpoints
    │   │   └── websocket.ts       # WebSocket hook for log/status streams
    │   ├── pages/
    │   │   ├── Dashboard.tsx      # Agent cards grid + portfolio PnL chart
    │   │   ├── AgentDetail.tsx    # Live status, trade history table, log stream
    │   │   └── Launch.tsx         # New agent wizard form
    │   └── components/
    │       ├── AgentCard.tsx      # Status badge, PnL, strategy, controls
    │       ├── LogViewer.tsx      # WebSocket-backed scrolling log
    │       ├── PnLChart.tsx       # Recharts trade history chart
    │       └── KillSwitch.tsx     # Global emergency stop button
    └── package.json
```

### HubClient SDK

```python
class HubClient:
    def __init__(self, hub_url: str, token: str | None = None, api_key: str | None = None)

    # Auth
    async def login(self, email: str, password: str) -> str           # returns JWT
    async def register(self, email: str, password: str) -> str

    # Agents
    async def list_agents(self) -> list[AgentInfo]
    async def create_agent(self, config: AgentCreateRequest) -> AgentInfo
    async def start_agent(self, agent_id: str) -> AgentInfo
    async def stop_agent(self, agent_id: str) -> None
    async def delete_agent(self, agent_id: str) -> None
    async def kill_all(self) -> None
    async def get_status(self, agent_id: str) -> StatusResponse
    async def get_logs(self, agent_id: str, limit: int = 200) -> list[LogEntry]
    async def get_metrics(self, agent_id: str) -> AgentMetrics

    # Streaming
    async def stream_logs(self, agent_id: str) -> AsyncIterator[LogEntry]
    async def stream_status(self, agent_id: str) -> AsyncIterator[StatusResponse]

    # Market
    async def get_price(self, symbol: str) -> float
    async def get_candles(self, symbol: str, interval: str) -> list[Candle]
```

---

## Docker and Networking

### Hub Compose

```yaml
# artic-hub/docker-compose.yml
services:
  hub:
    build: .
    ports:
      - "9000:9000"        # Hub API exposed to clients
    environment:
      - DATABASE_URL=postgresql+asyncpg://artic:artic@db:5432/artic
    depends_on:
      db:
        condition: service_healthy
    networks:
      - artic-net

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: artic
      POSTGRES_PASSWORD: artic
      POSTGRES_DB: artic
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U artic"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - artic-net

networks:
  artic-net:
    name: artic-net
    driver: bridge

volumes:
  pgdata:
```

### Agent Container Lifecycle

```
Hub receives POST /api/agents/{id}/start
  1. Pull artic-app:latest image (or build locally)
  2. docker.containers.run(
       image="artic-app:latest",
       name=f"artic-agent-{agent_id}",
       network="artic-net",              ← same bridge as hub
       ports={"8000/tcp": allocated_port},
       environment={
         "HUB_URL": "http://hub:9000",
         "HUB_AGENT_ID": agent_id,
         "SYMBOL": config.symbol,
         "AMOUNT_USDT": config.amount_usdt,
         "LEVERAGE": config.leverage,
         ... all other config fields ...
         "TWELVE_DATA_API_KEY": ...,
         "LLM_PROVIDER": config.llm_provider,
         "LLM_API_KEY": ...,              ← injected at spawn, never stored
         "LIVE_MODE": config.live_mode,
         "HASHKEY_API_KEY": ...,          ← injected at spawn if live_mode=true
         "HASHKEY_SECRET": ...,
       },
       restart_policy={"Name": "on-failure", "MaximumRetryCount": 3},
       mem_limit="512m",
       detach=True,
     )
  3. Poll http://artic-agent-{id}:8000/health every 500ms, timeout 20s
  4. POST http://artic-agent-{id}:8000/start with StartRequest
  5. Mark agent alive=True in DB
  6. Register in port registry
```

Hub reaches agents via Docker internal DNS (`http://artic-agent-{id}:8000`), so no host port exposure is needed between hub and agents. Host ports are only allocated for direct debug access.

---

## Agent Lifecycle State Machine

```
         create
            │
            ▼
        ┌────────┐
        │ stopped│◄─────────────────────────────┐
        └───┬────┘                              │
            │ start                             │
            ▼                                   │
        ┌──────────┐   health timeout           │
        │ starting │──────────────────────────► error
        └────┬─────┘                             │
             │ /health OK + /start OK            │
             ▼                                   │
         ┌───────┐    drawdown limit             │
         │ alive │──────────────────────────────►│
         └───┬───┘    crash / OOM               │
             │ stop                              │
             ▼                                   │
        ┌──────────┐                            │
        │ stopping │──────────────────────────► stopped
        └──────────┘   container stopped
```

---

## Data Flow — Full Request Cycle

```
User (any client)
  │
  │  POST /api/agents/abc123/start   [JWT in header]
  ▼
artic-hub / agents/router.py
  │  verify JWT → get user → check agent belongs to user
  │
  ▼
agents/service.py
  │  allocate port (atomic lock)
  │  inject env vars (including API keys — memory only, not stored)
  │
  ▼
docker/manager.py
  │  docker.containers.run(artic-app, env=..., network=artic-net)
  │
  ▼
docker/health.py
  │  poll GET http://artic-agent-abc123:8000/health
  │
  ▼
agents/service.py
  │  POST http://artic-agent-abc123:8000/start  {StartRequest}
  │  update agents table: status=alive, container_id=..., port=...
  │
  ▼
Response to client: AgentInfo {status: "alive", ...}

  ─────────── [agent now running] ───────────

artic-app / engine.py (every tick)
  │  POST http://hub:9000/internal/agents/abc123/status  {StatusResponse}
  │  POST http://hub:9000/internal/logs  {[LogEntry, ...]}  (batched)
  │
  ▼
artic-hub / internal/router.py
  │  upsert status in memory registry
  │  bulk insert log_entries to DB
  │
  ▼
artic-hub / ws/broadcaster.py
  │  push status / logs to all WS clients subscribed to agent abc123
  │
  ▼
artic-client (TUI / web / CLI --follow)
  receives real-time updates
```

---

## Security Model

| Concern | Approach |
|---------|----------|
| Client → Hub auth | JWT (15min expiry) + refresh token, or long-lived API key |
| API key storage | SHA-256 hash stored in DB, raw key shown once on creation |
| Agent endpoints | Only reachable inside artic-net bridge network, never exposed publicly |
| LLM / exchange API keys | Passed as env vars at container spawn, never persisted to DB |
| HashKey private key | Encrypted at rest with Fernet (symmetric), key from env var |
| Hub → agent comms | Internal Docker network only, no TLS needed |
| Client → Hub TLS | Terminate SSL at reverse proxy (nginx / Caddy) in production |

---

## Phase Roadmap Summary

| Phase | Weeks | Milestone |
|-------|-------|-----------|
| 0 — Foundation | 1–2 | Repos set up, Dockerized app boots, DB connected |
| 1 — Orchestration | 3–4 | Hub spawns agents, agent reports back, trades in DB |
| 2 — Auth + Persistence | 5 | JWT auth, user-scoped agents, logs survive restarts |
| 3 — Market Cache | 6 | Shared candle cache, Twelve Data rate limit solved |
| 4 — SDK + CLI | 7 | HubClient complete, CLI functional, TUI refactored |
| 5 — WebSocket | 8 | Real-time log/status streaming to all clients |
| 6 — Telegram Bot | 9 | Full bot control, push alerts |
| 7 — Web Dashboard | 10–11 | React dashboard, live logs, PnL charts |
| 8 — Risk Layer | 12 | Drawdown guard, kill-all, session limits |
| 9 — Live Trading | 13–14 | HashKey executor, encrypted keys, mainnet trades |

---

## Known Limitations (Inherited, To Be Fixed)

| Issue | Fix Phase |
|-------|-----------|
| Port race condition in `_next_port()` | Phase 1 — atomic lock in `docker/ports.py` |
| In-memory position state lost on restart | Phase 1 — agent POSTs every state change to hub |
| API keys not persisted across TUI restarts | Phase 1 — injected via Docker env at spawn |
| Twelve Data 8 calls/min shared across agents | Phase 3 — shared hub cache |
| Pyth feed IDs hardcoded (27 symbols only) | Phase 3 — dynamic Hermes lookup |
| `funding_bias_stub` returns 0 | Phase 9 — live via HashKey `get_funding_rate` |
| No session drawdown guard | Phase 8 |
| No global kill switch | Phase 8 |
| Blockchain executor is a stub | Phase 9 — HashKey REST executor |