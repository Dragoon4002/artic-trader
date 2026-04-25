# Artic — AI-Powered Multi-Agent Crypto Trading Platform

## Initia Hackathon Submission

- **Project Name**: Artic

### Project Overview

Artic is an LLM-orchestrated multi-agent paper-trading platform built on its
own Initia EVM rollup. Each user gets isolated agent containers (one per
symbol) where Gemini 2.5 Pro selects from 30+ quantitative strategies and
supervises risk in real time. Every supervisor decision and trade close is
written immutably to `DecisionLogger` / `TradeLogger` contracts on the
rollup — turning the dashboard into a forensic audit log of why the AI
acted, not just what it did.

### Implementation Detail

- **The Custom Implementation**: Hub orchestrates per-user Morph VMs that
  spawn Docker agent containers; each agent runs its own FastAPI trading
  loop with a 30+-strategy library and an LLM supervisor that re-plans every
  60s. Decisions and trades are hashed and emitted on-chain via web3.py from
  inside the agent container. Live log + decision streams ride a hub→VM
  WebSocket reverse proxy so the dashboard sees reasoning in real time.
- **The Native Feature**: **auto-signing** via InterwovenKit session keys.
  Agents bond a session-key grantee to the user's wallet and submit on-chain
  log txs with no per-tx popup. This is the autonomy primitive — without it,
  every supervisor tick would block on a wallet prompt. Identity is also
  surfaced via **Initia Usernames** (`.init`) wherever the wallet is shown.

### How to Run Locally

1. `cp .env.dev .env` and fill in `INITIA_RPC_URL`, `INITIA_PRIVATE_KEY`,
   `INITIA_CHAIN_ID` (your rollup chain ID from `weave init`).
2. `docker compose -f docker-compose.dev.yml up --build` — boots hub +
   user-server + Postgres.
3. `cd clients/web && bun install && bun dev` — dashboard at
   `http://localhost:3000`. Connect via InterwovenKit, click Settings →
   Enable Auto-Sign, then create an agent.
4. Optional — redeploy contracts to your rollup:
   `INITIA_RPC_URL=… INITIA_PRIVATE_KEY=… INITIA_CHAIN_ID=… python contracts/deploy.py && python contracts/deploy_trade_logger.py`.

Submission manifest: [`.initia/submission.json`](.initia/submission.json).

---

Artic is a production-ready, LLM-orchestrated trading platform. A central **Hub** server spawns and manages isolated **Agent** containers — one per trading symbol — each running its own FastAPI trading engine backed by 30+ quantitative strategies. An LLM supervisor selects strategies and manages risk dynamically in real time. Four client interfaces (TUI, CLI, Telegram bot, and a Next.js web app) all connect exclusively through the Hub.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Module Reference](#module-reference)
   - [Hub (Orchestrator)](#hub-orchestrator)
   - [App (Trading Engine)](#app-trading-engine)
   - [Strategies](#strategies)
   - [TUI Client](#tui-client)
   - [CLI Client](#cli-client)
   - [Telegram Bot](#telegram-bot)
   - [Web Client](#web-client)
4. [Smart Contracts](#smart-contracts)
   - [DecisionLogger.sol](#decisionloggersol)
   - [TradeLogger.sol](#tradeloggersol)
   - [Deployment Scripts](#deployment-scripts)
   - [Deployed Addresses](#deployed-addresses)
   - [On-chain Integration](#on-chain-integration)
5. [Database Schema](#database-schema)
6. [Authentication & Secrets](#authentication--secrets)
7. [Service Map & Call Graph](#service-map--call-graph)
8. [Environment Variables](#environment-variables)
9. [Installation & Setup](#installation--setup)
10. [Running the Platform](#running-the-platform)
11. [Tests](#tests)
12. [Utility Scripts](#utility-scripts)
13. [Documentation Index](#documentation-index)
14. [Design Principles](#design-principles)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENTS                               │
│   ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│   │   TUI   │  │   CLI   │  │ Telegram │  │  Web (docs) │  │
│   └────┬────┘  └────┬────┘  └────┬─────┘  └──────┬──────┘  │
│        └────────────┴────────────┘                │         │
│                      │ REST + WebSocket            │ Static  │
└──────────────────────┼────────────────────────────┘─────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                     HUB  (port 9000)                         │
│  Auth · Agent Registry · DB · Market Cache · WS Broadcaster  │
└─────────┬──────────────────────────────────────┬────────────┘
          │ Docker spawn / HTTP health            │ Push: status/trades/logs
          ▼                                       │
┌─────────────────────┐            ┌──────────────┴───────────┐
│  Agent: BTCUSD      │            │  Agent: ETHUSD           │
│  port 8000          │ …          │  port 8001               │
│  30+ quant algos    │            │  30+ quant algos         │
│  LLM planner        │            │  LLM planner             │
└─────────────────────┘            └──────────────────────────┘
          │                                       │
          └──────────────┬────────────────────────┘
                         ▼
          ┌──────────────────────────┐
          │   HashKey Chain (EVM)    │
          │   DecisionLogger.sol     │
          │   TradeLogger.sol        │
          └──────────────────────────┘
```

**Hub-spoke model.** The hub is the single source of truth for user data, agent state, and candle cache. Clients never talk to agent containers directly. Agents are stateless; all persistent data flows back to the hub's PostgreSQL database via the `/internal` push endpoints.

---

## Repository Structure

```
hashkey/
├── hub/                        # Central orchestrator (FastAPI, PostgreSQL)
│   ├── server.py               # App entry point, route registration
│   ├── config.py               # Env-based Pydantic settings
│   ├── client.py               # SDK used by all clients (HTTP + WS)
│   ├── Dockerfile              # Hub container image
│   ├── agents/
│   │   ├── router.py           # /api/agents/* REST endpoints
│   │   ├── service.py          # Spawn/stop/status logic
│   │   └── registry.py         # In-memory agent state cache
│   ├── auth/
│   │   ├── router.py           # /auth/login, /auth/refresh
│   │   ├── service.py          # JWT + API key generation, bcrypt
│   │   └── deps.py             # FastAPI dep: get_current_user
│   ├── docker/
│   │   ├── manager.py          # Docker SDK: create/start/stop/remove
│   │   └── ports.py            # Thread-safe atomic port allocation
│   ├── db/
│   │   ├── base.py             # SQLAlchemy async engine + session factory
│   │   └── models/
│   │       ├── user.py         # users table
│   │       ├── agent.py        # agents table
│   │       ├── trade.py        # trades table
│   │       ├── log_entry.py    # log_entries table
│   │       ├── market_cache.py # market_cache table
│   │       ├── secret.py       # user_secrets + agent_secret_overrides
│   │       └── onchain.py      # onchain_decisions table
│   ├── market/
│   │   ├── router.py           # /api/market/candles endpoint
│   │   ├── price_feed.py       # Price data sources
│   │   └── pyth_proxy.py       # Pyth Hermes proxy
│   ├── market_cache/
│   │   └── service.py          # APScheduler refresh loop (60s staleness)
│   ├── secrets/
│   │   └── service.py          # AES encrypt/decrypt, resolution order
│   ├── internal/
│   │   └── router.py           # /internal/agents/{id}/status|trades|logs
│   ├── ws/
│   │   ├── manager.py          # WebSocket connection pool
│   │   └── broadcaster.py      # Poll agents, push to WS clients
│   ├── utils/
│   │   └── symbols.py          # Symbol validation
│   └── alembic/                # Database migrations
│
├── app/                        # Trading engine (one Docker container per symbol)
│   ├── main.py                 # FastAPI: /health /start /stop /status /logs /plan
│   ├── Dockerfile              # Agent container image
│   ├── config.py               # Env-based Pydantic settings
│   ├── schemas.py              # Shared Pydantic types: Candle, StrategyPlan…
│   ├── engine.py               # Main trading loop orchestration
│   ├── log_buffer.py           # Circular in-memory log buffer (1000 entries)
│   ├── hub_callback.py         # Push status/trades/logs to hub
│   ├── onchain_logger.py       # Log decisions to HashKey Chain (DecisionLogger)
│   ├── onchain_trade_logger.py # Log trades to HashKey Chain (TradeLogger)
│   ├── market/
│   │   ├── market.py           # Fetch candles from hub cache
│   │   ├── pyth_client.py      # Pyth Hermes live prices (27 symbols)
│   │   ├── cmc_client.py       # CoinMarketCap token metadata
│   │   ├── market_analysis.py  # Technical indicators: ATR, vol, ADX, RSI
│   │   ├── token_analysis.py   # LLM fundamental token analysis
│   │   ├── cache_refresh.py    # Background cache refresh
│   │   ├── price_listener.py   # Price stream listener
│   │   └── db.py               # Local DB helpers
│   ├── llm/
│   │   ├── llm_planner.py      # Strategy selection + risk supervisor
│   │   └── chat.py             # Copilot chat interface
│   ├── executor/
│   │   ├── base.py             # BaseExecutor ABC
│   │   ├── paper.py            # Paper trading (in-memory positions)
│   │   └── hashkey.py          # HashKey Global REST API (live, TODO)
│   └── strategies/
│       ├── signals.py          # Dispatcher: strategy name → algo function
│       └── quant_algos/
│           ├── momentum_algos.py       # 8 momentum algorithms
│           ├── mean_reversion_algos.py # 6 mean-reversion algorithms
│           ├── volatility_algos.py     # 3 volatility algorithms
│           ├── volume_algos.py         # 3 volume algorithms
│           ├── statistical_algos.py    # 2 statistical algorithms
│           ├── risk_sizing.py          # Kelly criterion, vol scaling
│           └── time_filters.py         # Session + day-of-week filters
│
├── clients/
│   ├── tui/
│   │   ├── tui.py              # Textual app: 5 screens
│   │   ├── hub_adapter.py      # HubClient wrapper, 2s poll
│   │   ├── login_screen.py     # Auth dialog
│   │   └── __main__.py
│   ├── cli/
│   │   ├── cli.py              # Arg parsing, command execution
│   │   └── __main__.py
│   ├── telegram/
│   │   ├── bot.py              # Webhook registration, command routing
│   │   ├── formatter.py        # Telegram markdown formatting
│   │   └── __main__.py
│   └── web/                    # Next.js 15 landing + docs site
│       ├── app/
│       │   ├── page.tsx        # Landing page
│       │   ├── layout.tsx      # Root layout
│       │   ├── globals.css     # Design system (CSS custom props)
│       │   ├── blog/           # Blog posts
│       │   ├── docs/           # 10 MDX doc pages
│       │   ├── jobs/           # Careers page
│       │   └── litepaper/      # Litepaper page
│       ├── components/
│       │   ├── landing/        # Hero, features grid, navbar, footer (15 files)
│       │   ├── docs/           # Sidebar, callout, code-tabs
│       │   ├── shared/         # Logo, FadeIn
│       │   └── ui/             # shadcn/ui: Button, Card, Tabs, Table…
│       ├── lib/
│       │   ├── docs-nav.ts     # Sidebar navigation structure
│       │   └── utils.ts        # Utility functions
│       ├── mdx-components.tsx  # MDX element overrides
│       ├── next.config.ts      # Next.js config
│       └── package.json        # Next.js 15, shadcn/ui, Tailwind v4
│
├── contracts/                  # Solidity smart contracts
│   ├── DecisionLogger.sol      # Logs LLM trading decisions on-chain
│   ├── TradeLogger.sol         # Logs trade open/close events on-chain
│   ├── deploy.py               # Deploy DecisionLogger → deployed.json
│   ├── deploy_trade_logger.py  # Deploy TradeLogger → trade_logger_deployed.json
│   ├── deployed.json           # DecisionLogger address + ABI (auto-generated)
│   └── trade_logger_deployed.json  # TradeLogger address + ABI (auto-generated)
│
├── docs/                       # Architecture + protocol documentation
│   ├── CLAUDE.md               # Doc index
│   ├── architecture/
│   │   ├── overview.md         # System topology, data flow, invariants
│   │   └── data-model.md       # 8 tables, columns, relationships, rules
│   └── connections/
│       ├── service-map.md      # Call graph, port map, rate limits
│       ├── auth-flow.md        # JWT + API key auth, secrets encryption
│       └── env-secrets.md      # Secret resolution order, all known keys
│
├── tests/                      # pytest test suite
│   ├── CLAUDE.md               # Test index + conventions
│   ├── hub/                    # Auth, agents, WebSocket, secrets, market
│   ├── app/                    # Engine, market data, LLM, executors
│   │   ├── strategies/         # All 30+ algo correctness tests
│   │   └── pyth_api_connection/
│   └── clients/                # TUI, CLI, Telegram
│
├── scripts/                    # Utility + migration scripts
│   ├── build-app-image.sh      # Build agent Docker image
│   ├── setup-network.sh        # Create Docker bridge network
│   ├── migrate_add_columns.py  # Alembic migration helper
│   └── migrate_add_columns.sql # Raw SQL migration
│
├── docker-compose.yml          # Hub + network definition
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── copyright.txt               # License
```

---

## Module Reference

### Hub (Orchestrator)

**Location:** `/hub/`
**Port:** `9000`
**Container:** `hub/Dockerfile` — Python 3.12, mounts Docker socket for agent spawning

The hub is the platform's central nervous system. It owns authentication, agent lifecycle, candle caching, WebSocket broadcasting, and all persistent state. No client touches an agent directly — everything proxies through the hub.

#### Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastAPI app setup, router includes, CORS, middleware |
| `config.py` | `HubSettings` — reads `DATABASE_URL`, `INTERNAL_SECRET`, `JWT_SECRET`, etc. from env |
| `client.py` | Python SDK used by TUI, CLI, and Telegram. Provides typed async methods for every hub endpoint |
| `agents/service.py` | `AgentService.spawn()` — pulls agent image, creates container with env vars, waits for `/health`; `stop()` — gracefully stops and removes |
| `agents/router.py` | `POST /api/agents`, `GET /api/agents`, `GET /api/agents/{id}`, `DELETE /api/agents/{id}` |
| `agents/registry.py` | `AgentRegistry` — thread-safe in-memory dict of live agent states; periodically reconciled from DB |
| `auth/service.py` | `create_access_token()`, `create_refresh_token()`, `hash_api_key()` (SHA-256), `verify_password()` (bcrypt) |
| `auth/router.py` | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` |
| `auth/deps.py` | `get_current_user` FastAPI dependency — validates JWT or API key header |
| `docker/manager.py` | `DockerManager` — wraps Docker SDK; `create_agent_container()`, `start()`, `stop()`, `remove()`, `get_logs()` |
| `docker/ports.py` | `PortAllocator` — thread-safe atomic counter starting at 8000; prevents port collisions when spawning multiple agents |
| `db/base.py` | `AsyncEngine` + `AsyncSessionLocal` factory; `init_db()` creates all tables |
| `market_cache/service.py` | `MarketCacheService` — APScheduler background job that refreshes TwelveData candles every 60 seconds per tracked symbol; caches to `market_cache` table |
| `internal/router.py` | `/internal/agents/{id}/status` (POST), `/internal/agents/{id}/trades` (POST), `/internal/agents/{id}/logs` (POST) — authenticated via `X-Internal-Secret` header |
| `ws/manager.py` | `ConnectionManager` — maintains `Dict[str, WebSocket]` per user; `connect()`, `disconnect()`, `broadcast()` |
| `ws/broadcaster.py` | `WsBroadcaster` — polls agents' `/status` every 2s and emits JSON diffs to connected WebSocket clients |
| `secrets/service.py` | AES-based `encrypt()` / `decrypt()`; `resolve_secret()` walks override hierarchy |

#### Hub API Endpoints (Summary)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create user account |
| POST | `/auth/login` | — | Get JWT access + refresh tokens |
| POST | `/auth/refresh` | Refresh token | Rotate access token |
| GET | `/api/agents` | JWT/API key | List user's agents |
| POST | `/api/agents` | JWT/API key | Spawn new agent container |
| GET | `/api/agents/{id}` | JWT/API key | Get agent status |
| DELETE | `/api/agents/{id}` | JWT/API key | Stop + remove agent |
| GET | `/api/agents/{id}/logs` | JWT/API key | Fetch agent log buffer |
| GET | `/api/agents/{id}/trades` | JWT/API key | Fetch trade history |
| GET | `/api/market/candles` | — | Get cached OHLCV candles |
| WS | `/ws` | JWT/API key | Real-time agent status stream |
| POST | `/internal/agents/{id}/status` | Internal secret | Agent pushes status |
| POST | `/internal/agents/{id}/trades` | Internal secret | Agent pushes closed trade |
| POST | `/internal/agents/{id}/logs` | Internal secret | Agent pushes log batch |

---

### App (Trading Engine)

**Location:** `/app/`
**Port:** `8000` (per container)
**Container:** `app/Dockerfile` — Python 3.12, one instance per symbol

Each agent container runs an independent FastAPI app with its own trading loop, LLM planner, and market data clients. The hub injects all configuration as environment variables at spawn time (symbol, interval, risk params, secrets).

#### Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app; `POST /start` triggers `engine.run()` in background task; `POST /stop` cancels it; `GET /status` returns live PnL snapshot; `GET /logs` returns buffer |
| `engine.py` | `Engine.run()` — main async loop: fetch Pyth price → get candles → run LLM planner → execute signal → update paper position → push to hub; 30s default tick |
| `schemas.py` | `Candle`, `StrategyPlan`, `TradeEvent`, `AgentStatus`, `LogEntry`, `RiskParams` — shared Pydantic types |
| `log_buffer.py` | `LogBuffer` — thread-safe circular deque (1000 entries); append with level + timestamp |
| `hub_callback.py` | `HubCallback.push_status()`, `.push_trade()`, `.push_logs()` — fire-and-forget async HTTP to hub's `/internal` endpoints with `X-Internal-Secret` header |
| `onchain_logger.py` | `OnchainLogger.log_decision()` — builds `sessionId` / `symbolBytes` / `reasoningHash` via keccak256, submits `logDecision()` tx to HashKey Chain; runs in thread pool to avoid blocking event loop |
| `onchain_trade_logger.py` | `OnchainTradeLogger.log_trade()` — scales prices by `1e8`, hashes JSON detail, submits `logTrade()` tx; disabled gracefully if `deployed.json` not found |
| `market/market.py` | `MarketClient.get_candles()` — fetches from hub's `/api/market/candles` (never direct TwelveData calls) |
| `market/pyth_client.py` | `PythClient.get_price()` / `.get_prices_batch()` — calls Pyth Hermes REST; 27 crypto feed IDs hardcoded; 3 retries, 0.3s backoff |
| `market/market_analysis.py` | `compute_atr()`, `compute_volatility()`, `compute_adx()`, `compute_rsi()` — returns dict of technical indicators for LLM context |
| `market/token_analysis.py` | `TokenAnalyzer.analyze()` — LLM call for fundamental token assessment (sentiment, macro context) |
| `llm/llm_planner.py` | `LLMPlanner.plan()` — assembles market context, calls LLM with tool-use spec, parses `StrategyPlan`; `LLMSupervisor.check()` — risk override layer |
| `llm/chat.py` | `CopilotChat.ask()` — conversational Q&A about agent strategy and position |
| `executor/base.py` | `BaseExecutor` ABC: `place_order()`, `get_positions()`, `close_position()` |
| `executor/paper.py` | `PaperExecutor` — in-memory `PaperPosition`; tracks long/short, computes PnL in bps |
| `executor/hashkey.py` | `HashkeyExecutor` — HashKey Global REST API integration (live trading, in progress) |

---

### Strategies

**Location:** `/app/strategies/`

The strategy layer consists of 30+ quantitative algorithms all implementing the same contract:

```python
def strategy_name(candles: list[dict], params: dict) -> tuple[float, str]:
    """
    candles: list of OHLCV dicts sorted oldest→newest
    returns: (signal, detail)
        signal: float in [-1.0, 1.0]  (-1=strong short, 0=flat, 1=strong long)
        detail: human-readable explanation string
    """
```

The LLM planner selects a strategy by name. `signals.py` dispatches to the correct function.

#### Algorithm Catalogue

| File | Count | Algorithms |
|------|-------|-----------|
| `momentum_algos.py` | 8 | `simple_momentum`, `dual_momentum`, `breakout_momentum`, `donchian_channel`, `ma_crossover`, `ema_crossover`, `macd_signal`, `ichimoku_signal` |
| `mean_reversion_algos.py` | 6 | `z_score_reversion`, `bollinger_reversion`, `rsi_signal`, `stochastic_signal`, `range_sr`, `mean_reversion_combo` |
| `volatility_algos.py` | 3 | `atr_breakout`, `bollinger_squeeze`, `keltner_bollinger_squeeze` |
| `volume_algos.py` | 3 | `vwap_deviation`, `obv_trend`, `funding_bias_stub` |
| `statistical_algos.py` | 2 | `linear_regression_channel`, `kalman_fair_value` |
| `risk_sizing.py` | 2 | `kelly_size`, `vol_scaling_mult` |
| `time_filters.py` | 2 | `session_filter`, `day_of_week_filter` |

**Total: 30+ algorithms**

Strategy indices are mapped 0–30 in `onchain_logger.py` (for on-chain logging) and 255 is reserved for `llm_auto` (LLM selects dynamically each tick).

---

### TUI Client

**Location:** `/clients/tui/`
**Framework:** [Textual](https://textual.textualize.io/) (Python)

A full terminal UI with 5 interactive screens:

| Screen | Purpose |
|--------|---------|
| `Dashboard` | Live agent grid — status, PnL, symbol, strategy per agent |
| `CreateAgent` | Form to configure and spawn a new agent |
| `AgentDetail` | Real-time logs, position details, trade history for one agent |
| `LogViewer` | Scrollable full log stream |
| `Theme` | Color theme switcher |

| File | Purpose |
|------|---------|
| `tui.py` | Main Textual `App` subclass; mounts screens, handles global key bindings |
| `hub_adapter.py` | Wraps `HubClient`; sets poll interval to 2 seconds; normalises responses for Textual widgets |
| `login_screen.py` | Login dialog (email + password or API key); stores JWT in adapter |
| `__main__.py` | `python -m clients.tui` entry point |

---

### CLI Client

**Location:** `/clients/cli/`

A scriptable command-line interface. Every command supports `--json` for machine-readable output (for piping, CI scripts, etc.).

| File | Purpose |
|------|---------|
| `cli.py` | `argparse`-based entry; subcommands: `login`, `agents list`, `agents start`, `agents stop`, `agents logs`, `agents status`, `market candles` |
| `__main__.py` | `python -m clients.cli` entry point |

```bash
# Examples
python -m clients.cli agents list --json
python -m clients.cli agents start --symbol BTCUSD --interval 30
python -m clients.cli agents stop <agent-id>
python -m clients.cli agents logs <agent-id> --tail 100
```

---

### Telegram Bot

**Location:** `/clients/telegram/`
**Library:** `python-telegram-bot >= 20.0`

Command set mirrors the hub SDK 1:1.

| File | Purpose |
|------|---------|
| `bot.py` | Webhook registration, command handler routing, inline keyboard support |
| `formatter.py` | Formats hub responses as Telegram Markdown (tables, status icons, PnL colours) |
| `__main__.py` | `python -m clients.telegram` entry point |

**Bot Commands:**

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + auth prompt |
| `/login <email> <password>` | Authenticate and store JWT in session |
| `/agents` | List all running agents |
| `/spawn <symbol>` | Start a new agent |
| `/stop <agent-id>` | Stop and remove an agent |
| `/status <agent-id>` | Real-time PnL snapshot |
| `/logs <agent-id>` | Last 20 log lines |

---

### Web Client

**Location:** `/clients/web/`
**Stack:** Next.js 15, TypeScript, Tailwind CSS v4, shadcn/ui, MDX

Static marketing and documentation site. Dark-only design with an orange/red/teal accent palette defined via CSS custom properties in `globals.css`.

#### App Pages

| Route | File | Description |
|-------|------|-------------|
| `/` | `app/page.tsx` | Landing page — hero, features grid, client showcase, CTA |
| `/docs/*` | `app/docs/*.mdx` | 10 documentation pages (see below) |
| `/blog/*` | `app/blog/` | Blog posts |
| `/jobs` | `app/jobs/` | Careers page |
| `/litepaper` | `app/litepaper/` | Litepaper |

#### Documentation Pages (MDX)

| Page | Content |
|------|---------|
| `architecture` | System topology, hub-spoke model, invariants |
| `authentication` | JWT flow, API keys, secret resolution |
| `clients` | Comparison of TUI, CLI, Telegram, Web |
| `cli-reference` | Full CLI command reference |
| `deployment` | Docker Compose setup, env vars |
| `hub-api` | Full Hub REST + WebSocket API reference |
| `quickstart` | 5-minute setup guide |
| `strategies` | Strategy catalogue, LLM selection, custom algos |
| `telegram-reference` | Bot command reference |
| `testing` | Test structure, conventions, running tests |
| `tui-reference` | TUI screen guide, keyboard shortcuts |

#### Components

| Folder | Files | Purpose |
|--------|-------|---------|
| `components/landing/` | 15 | `Hero`, `Features`, `Navbar`, `Footer`, `ClientCards`, `HowItWorks`, `CTA`, `PricingSection`, `FadeIn`, etc. |
| `components/docs/` | 5 | `Sidebar`, `DocNavigation`, `Callout`, `CodeTabs`, `MobileNav` |
| `components/shared/` | 2 | `Logo`, `FadeIn` |
| `components/ui/` | 10+ | shadcn/ui primitives: `Button`, `Card`, `Tabs`, `Table`, `Separator`, `Badge`, `Input`, etc. |

---

## Smart Contracts

The platform logs all LLM trading decisions and trade executions permanently to **HashKey Chain** using two Solidity event-emitting contracts. All sensitive data is stored as keccak256 hashes — only derived hashes and numeric metrics touch the chain.

---

### DecisionLogger.sol

**Location:** `contracts/DecisionLogger.sol`
**Purpose:** Emits a `DecisionLogged` event for every LLM decision (strategy selection + confidence + PnL feedback)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecisionLogger {
    event DecisionLogged(
        bytes32 indexed sessionId,   // keccak256(symbol + agentId + timestamp)
        bytes32 indexed symbol,      // e.g. bytes32("BTCUSD")
        uint8   action,              // 0=HOLD, 1=OPEN_LONG, 2=OPEN_SHORT, 3=CLOSE, 4=ADJUST
        uint8   strategy,            // index into strategy enum (0–30, 255=llm_auto)
        uint8   confidence,          // 0-100
        int16   pnlBps,             // PnL in basis points
        bytes32 reasoningHash       // keccak256 of full LLM reasoning text
    );

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function logDecision(
        bytes32 sessionId,
        bytes32 symbol,
        uint8 action,
        uint8 strategy,
        uint8 confidence,
        int16 pnlBps,
        bytes32 reasoningHash
    ) external onlyOwner {
        emit DecisionLogged(sessionId, symbol, action, strategy, confidence, pnlBps, reasoningHash);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
```

**Action enum:**

| Value | Meaning |
|-------|---------|
| `0` | HOLD |
| `1` | OPEN_LONG |
| `2` | OPEN_SHORT |
| `3` | CLOSE |
| `4` | ADJUST |

**Strategy index 0–30** maps to the 30+ quant algorithms; `255` = `llm_auto` (dynamic selection).

---

### TradeLogger.sol

**Location:** `contracts/TradeLogger.sol`
**Purpose:** Emits a `TradeLogged` event for each trade open or close event, including scaled prices and PnL

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TradeLogger {
    event TradeLogged(
        bytes32 indexed sessionId,   // keccak256(agentId + symbol + timestamp)
        bytes32 indexed symbol,      // keccak256(symbol)
        uint8   side,                // 0=OPEN_LONG, 1=OPEN_SHORT, 2=CLOSE_LONG, 3=CLOSE_SHORT
        uint128 entryPrice,          // scaled by 1e8
        uint128 exitPrice,           // 0 if open event
        int16   pnlBps,             // PnL in basis points (0 if open)
        bytes32 detailHash           // keccak256(JSON of full trade detail)
    );

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function logTrade(
        bytes32 sessionId,
        bytes32 symbol,
        uint8 side,
        uint128 entryPrice,
        uint128 exitPrice,
        int16 pnlBps,
        bytes32 detailHash
    ) external onlyOwner {
        emit TradeLogged(sessionId, symbol, side, entryPrice, exitPrice, pnlBps, detailHash);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
```

**Side enum:**

| Value | Meaning |
|-------|---------|
| `0` | OPEN_LONG |
| `1` | OPEN_SHORT |
| `2` | CLOSE_LONG |
| `3` | CLOSE_SHORT |

**Price scaling:** all prices are multiplied by `1e8` before storing on-chain (e.g. BTC at $65,000 → `6500000000000`).
**Privacy:** `detailHash` is `keccak256(json_string)` — full trade JSON is stored off-chain in PostgreSQL.

---

### Deployment Scripts

#### `contracts/deploy.py` — Deploy DecisionLogger

```python
"""Deploy DecisionLogger to HashKey Chain."""
# Requirements: pip install web3 py-solc-x
# Env vars:     HSK_RPC_URL, HSK_PRIVATE_KEY

python3 contracts/deploy.py
# Output: contracts/deployed.json
```

Steps performed:
1. Installs `solc 0.8.20` via `py-solc-x`
2. Compiles `DecisionLogger.sol`
3. Connects to `HSK_RPC_URL`
4. Signs + broadcasts deployment tx from `HSK_PRIVATE_KEY`
5. Waits for receipt (blocks until mined)
6. Writes `contracts/deployed.json` with address, ABI, tx_hash, block_number

#### `contracts/deploy_trade_logger.py` — Deploy TradeLogger

```python
"""Deploy TradeLogger to HashKey Chain."""
python3 contracts/deploy_trade_logger.py
# Output: contracts/trade_logger_deployed.json
```

Same steps as above, produces `contracts/trade_logger_deployed.json`.

---

### Deployed Addresses

**Network:** HashKey Chain Testnet (`https://testnet.hsk.xyz`)
**Deployer:** `0xbEff58504eB09E3Bb3edC68e81250c71D3f8c0f5`
**Deployed:** 2026-04-15

| Contract | Address | Deploy Tx | Block |
|----------|---------|-----------|-------|
| `DecisionLogger` | `0x70a15Db526104abC2f021b7c690cd89a07EDE49C` | `2d72a182ce20453680396e6561fc948276dcce416b2844f6c460c5234f1264dd` | 26543461 |
| `TradeLogger` | `0xeeb56334152D6bDB62aacF56f8DbCceA5210b78D` | `a159d64f5bb1dfcd2ce88d50255a4f71f6b0280607a1f802ed7899268b3cb16c` | 26543465 |

**Verification txs (post-deploy test calls):**

| Call | Tx Hash | Result |
|------|---------|--------|
| `DecisionLogger.logDecision()` | `d1e9fd4bf2c02c8f3f6197b675f8f7edf3096e46b59dbdac7673e3f1b6d90072` | `DecisionLogged` event emitted — action=1 (OPEN_LONG), confidence=85 |
| `TradeLogger.logTrade()` | `138cac10c95f8c985f90ed250511ad437f168427c5b959f2b2fead33e50fa6b9` | `TradeLogged` event emitted — side=0 (OPEN_LONG), entryPrice=6500000000000 |

---

### On-chain Integration

**`app/onchain_logger.py`** — `OnchainLogger`

Loaded by the trading engine on startup. Reads `contracts/deployed.json` for contract address and ABI. Disabled gracefully (returns `None`) if either env var or JSON file is absent.

```python
# Called in engine.py after each LLM decision
await self._onchain_logger.log_decision(
    agent_id=self._agent_id,
    symbol="BTCUSD",
    action="OPEN_LONG",
    strategy="ema_crossover",
    confidence=85,
    pnl_bps=120,
    reasoning="EMA 9 crossed above EMA 21 with strong volume..."
)
```

Internally:
- `sessionId = keccak256(symbol + agentId + timestamp)`
- `symbolBytes = keccak256(symbol)[:32]`
- `reasoningHash = keccak256(reasoning_text)`
- tx submitted via `asyncio.get_event_loop().run_in_executor()` to avoid blocking the trading loop

**`app/onchain_trade_logger.py`** — `OnchainTradeLogger`

Reads `contracts/trade_logger_deployed.json`. Called on position open and close events.

```python
await self._trade_logger.log_trade(
    agent_id=self._agent_id,
    symbol="BTCUSD",
    side="OPEN_LONG",
    entry_price=65000.0,
    exit_price=0.0,       # 0 for open events
    pnl_bps=0,
    detail_json='{"size": 0.01, "leverage": 1}'
)
```

**`hub/db/models/onchain.py`** — ORM tables for off-chain mirror of on-chain events:

| Table | Columns |
|-------|---------|
| `onchain_decisions` | id, agent_id, session_id, tx_hash, block_number, reasoning_text, created_at |
| `onchain_trades` | id, agent_id, tx_hash, side, entry_price, exit_price, pnl_bps, detail_json, block_number, created_at |

---

## Database Schema

**Engine:** PostgreSQL (async via `asyncpg`)
**ORM:** SQLAlchemy async
**Migrations:** Alembic (`hub/alembic/`)

### Tables

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Auto-generated |
| `email` | VARCHAR UNIQUE | Login identifier |
| `password_hash` | VARCHAR | bcrypt |
| `api_key_hash` | VARCHAR | SHA-256 of raw API key |
| `created_at` | TIMESTAMP | Auto |

#### `agents`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | All queries must filter by this |
| `symbol` | VARCHAR | e.g. `BTCUSD` |
| `container_id` | VARCHAR | Docker container ID |
| `port` | INTEGER | Allocated port (8000+) |
| `status` | VARCHAR | `running`, `stopped`, `error` |
| `strategy_name` | VARCHAR | Active strategy or `llm_auto` |
| `interval_seconds` | INTEGER | Tick interval |
| `risk_params` | JSONB | `max_drawdown`, `position_size_pct`, etc. |
| `live_mode` | BOOLEAN | Paper vs live trading |

#### `trades`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → agents | |
| `side` | VARCHAR | `LONG` or `SHORT` |
| `entry_price` | FLOAT | |
| `exit_price` | FLOAT | NULL if open |
| `pnl` | FLOAT | In USD |
| `opened_at` | TIMESTAMP | |
| `closed_at` | TIMESTAMP | NULL if open |

#### `log_entries`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → agents | |
| `level` | VARCHAR | `init`, `llm`, `action`, `error`, etc. |
| `message` | TEXT | |
| `timestamp` | TIMESTAMP | |

**Rule:** Append-only. Bulk-inserted every 10 ticks.

#### `market_cache`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `symbol` | VARCHAR | |
| `timeframe` | VARCHAR | e.g. `1h`, `15m` |
| `candles` | JSONB | Array of OHLCV dicts |
| `last_fetched` | TIMESTAMP | Stale if > 60s ago |

#### `user_secrets`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `key_name` | VARCHAR | e.g. `TWELVE_DATA_API_KEY` |
| `encrypted_value` | TEXT | AES encrypted |

#### `agent_secret_overrides`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → agents | |
| `key_name` | VARCHAR | |
| `encrypted_value` | TEXT | AES encrypted |

#### `onchain_decisions`
| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `agent_id` | UUID FK → agents | |
| `session_id` | VARCHAR | keccak256 hex |
| `tx_hash` | VARCHAR | HashKey Chain tx hash |
| `block_number` | INTEGER | |
| `reasoning_text` | TEXT | Full LLM reasoning (off-chain copy) |
| `created_at` | TIMESTAMP | |

### Relationships

```
users 1──* agents
agents 1──* trades
agents 1──* log_entries
agents 1──* agent_secret_overrides
agents 1──* onchain_decisions
users  1──* user_secrets
```

---

## Authentication & Secrets

### Auth Methods

| Method | Used By | Transport | How |
|--------|---------|-----------|-----|
| JWT | TUI, web | `Authorization: Bearer <token>` | `POST /auth/login` → 15min access + 7-day refresh |
| API Key | CLI, Telegram | `X-API-Key: <key>` | Raw key displayed once on register; SHA-256 stored in DB |
| Internal Secret | Agent → Hub | `X-Internal-Secret: <secret>` | Injected via env at container spawn; never user-visible |

### Secret Resolution Order (highest wins)

```
1. Ephemeral override   (per-request, never stored)
2. agent_secret_overrides  (per-agent, AES encrypted in DB)
3. user_secrets            (user-level, AES encrypted in DB)
4. .env / process env      (host fallback)
```

### Auth Flow (JWT)

```
Client          Hub                    DB
  │─POST /auth/login──────────────────►│
  │             │─verify bcrypt hash──►│
  │             │◄─user row────────────│
  │◄─{access_token, refresh_token}─────│
  │
  │─GET /api/agents (Authorization: Bearer <token>)
  │             │─decode JWT, check exp│
  │             │─extract user_id──────│
  │◄─agents list────────────────────────│
```

---

## Service Map & Call Graph

| Caller | Callee | Protocol | Auth | Notes |
|--------|--------|----------|------|-------|
| TUI / CLI / Telegram | Hub `:9000` | REST + WS | JWT or API key | All client traffic |
| Hub | Agent `:8000+` | HTTP | — | Health check, start, stop at spawn |
| Agent | Hub `/internal/*` | HTTP | `X-Internal-Secret` | Push status, trades, logs |
| Agent | Hub `/api/market/candles` | HTTP | — | Cached candles |
| Agent | Pyth Hermes | REST | — | Live prices, free, unlimited |
| Hub | TwelveData | REST | API key | OHLCV candles, 8 req/min rate limit |
| Agent | LLM provider | REST | API key | Strategy selection, risk analysis |
| Hub | PostgreSQL | SQL | DB credentials | All persistent state |
| Agent | HashKey Chain | RPC | Private key | `logDecision()`, `logTrade()` |

### Port Map

| Service | Port | Binding |
|---------|------|---------|
| Hub | `9000` | `0.0.0.0` |
| Agent containers | `8000`, `8001`, `8002` … | Docker internal, allocated atomically |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# ── Market Data ─────────────────────────────────────────────────────────────
CMC_API_KEY=                        # CoinMarketCap token metadata (optional)
TWELVE_DATA_API_KEY=                # OHLCV candle data (required for strategies)

# ── MongoDB Cache (optional) ─────────────────────────────────────────────────
MONGODB_URI=                        # Atlas URI; omit to skip caching

# ── LLM Providers (at least one required) ────────────────────────────────────
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
LLM_PROVIDER=gemini                 # openai | anthropic | deepseek | gemini
LLM_MODEL=gemini-2.5-flash

# ── Hub Infrastructure ───────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
INTERNAL_SECRET=<random 40+ char>   # Agent → Hub auth
JWT_SECRET=<random 40+ char>        # JWT signing key

# ── Telegram Bot ─────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=

# ── HashKey Global Exchange (live trading) ───────────────────────────────────
HASHKEY_API_KEY=
HASHKEY_SECRET=
HASHKEY_SANDBOX=true

# ── HashKey Chain On-chain Logging ───────────────────────────────────────────
HSK_RPC_URL=https://testnet.hsk.xyz
HSK_PRIVATE_KEY=<deployer private key>
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- Docker + Docker Compose
- PostgreSQL (or Neon serverless)
- Node.js 20+ (for web client)

### 1. Python Dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `fastapi`, `uvicorn`, `httpx`, `pydantic`, `pydantic-settings`
- `sqlalchemy[asyncio]`, `asyncpg`, `alembic`
- `PyJWT`, `passlib[bcrypt]`, `docker`
- `openai`, `anthropic`
- `python-telegram-bot>=20.0`, `textual`
- `web3`, `py-solc-x`
- `APScheduler`, `websockets`

### 2. Database

```bash
# Run Alembic migrations
alembic upgrade head
```

### 3. Docker Network

```bash
bash scripts/setup-network.sh
# Creates Docker bridge network: artic-net
```

### 4. Build Agent Image

```bash
bash scripts/build-app-image.sh
# Builds: artic-agent:latest from app/Dockerfile
```

### 5. Web Client

```bash
cd clients/web
npm install
npm run build
npm start
# Development: npm run dev
```

### 6. Deploy Smart Contracts

```bash
# Set env vars
export HSK_RPC_URL=https://testnet.hsk.xyz
export HSK_PRIVATE_KEY=<your_key>

# Deploy both contracts
python3 contracts/deploy.py
python3 contracts/deploy_trade_logger.py

# Output: contracts/deployed.json + contracts/trade_logger_deployed.json
```

---

## Running the Platform

### Start Hub

```bash
docker-compose up -d
# Hub available at http://localhost:9000
```

Or directly:

```bash
python -m hub.server
```

### Start TUI Client

```bash
python -m clients.tui
```

### Start CLI Client

```bash
python -m clients.cli --help
python -m clients.cli login --email you@example.com --password yourpass
python -m clients.cli agents start --symbol BTCUSD
```

### Start Telegram Bot

```bash
python -m clients.telegram
```

---

## Tests

**Framework:** `pytest` with `pytest-asyncio`
**Mock policy:** All external APIs (Pyth, TwelveData, LLM, Docker, HashKey Chain) are mocked — no real network calls in tests.

```bash
# Run all tests
pytest tests/

# Run by module
pytest tests/hub/
pytest tests/app/
pytest tests/app/strategies/
pytest tests/clients/
```

| Folder | What's tested |
|--------|---------------|
| `tests/hub/` | Auth endpoints, agent CRUD, WebSocket streams, secrets encryption, market cache service |
| `tests/app/` | Engine loop, Pyth client, market analysis, LLM planner, paper executor |
| `tests/app/strategies/` | All 30+ algorithms — verifies `(signal, detail)` return contract; signal ∈ `[-1.0, 1.0]` |
| `tests/clients/tui/` | Screen rendering, hub adapter polling, login dialog |
| `tests/clients/cli/` | Command parsing, `--json` output format |
| `tests/clients/telegram/` | Command handler dispatch, formatter output |

**Conventions:**
- Strategy tests pass only candle arrays (no live prices)
- All DB tests use an isolated in-memory SQLite session
- Hub agent queries always filter by `user_id` (multi-tenant isolation)

---

## Utility Scripts

| Script | Usage | Description |
|--------|-------|-------------|
| `scripts/build-app-image.sh` | `bash scripts/build-app-image.sh` | Builds `artic-agent:latest` Docker image |
| `scripts/setup-network.sh` | `bash scripts/setup-network.sh` | Creates `artic-net` Docker bridge network |
| `scripts/migrate_add_columns.py` | `python3 scripts/migrate_add_columns.py` | Runs Alembic column-addition migration |
| `scripts/migrate_add_columns.sql` | `psql -f scripts/migrate_add_columns.sql` | Raw SQL version of same migration |

---

## Documentation Index

| Doc | Location | Content |
|-----|----------|---------|
| Architecture Overview | `docs/architecture/overview.md` | System topology, Mermaid diagram, invariants, data flow |
| Data Model | `docs/architecture/data-model.md` | All 8 tables, column types, FK relationships, constraints |
| Service Map | `docs/connections/service-map.md` | Full call graph, port assignments, rate limits |
| Auth Flow | `docs/connections/auth-flow.md` | JWT + API key auth, secrets encryption walkthrough |
| Env & Secrets | `docs/connections/env-secrets.md` | Secret resolution order, all known keys, encryption details |
| Hub Guide | `hub/CLAUDE.md` | Folder map, endpoint list, key dependencies |
| App Guide | `app/CLAUDE.md` | Engine loop, market data flow, LLM planning |
| Strategies Guide | `app/strategies/CLAUDE.md` | Algorithm contract, naming conventions, adding new algos |
| TUI Guide | `clients/tui/CLAUDE.md` | Screens, keybindings, hub adapter |
| CLI Guide | `clients/cli/CLAUDE.md` | Commands, `--json` contract |
| Telegram Guide | `clients/telegram/CLAUDE.md` | Command list, formatter |
| Web Guide | `clients/web/CLAUDE.md` | Stack, design system, MDX docs |
| Tests Guide | `tests/CLAUDE.md` | Test index, mock conventions, CI setup |

---

## Design Principles

### Hub-Spoke
Hub is the single source of truth. Clients never talk to agents directly. Agents are side-effect nodes — compute + push, nothing more.

### Stateless Agents
Agent containers hold no durable state. Killing a container loses nothing — all trades, logs, and decisions have already been pushed to the hub's PostgreSQL via the `/internal` endpoints. Position snapshots only.

### LLM-Driven Strategy Selection
The LLM doesn't write code — it selects from a fixed, auditable library of 30+ algorithms by name, and the `signals.py` dispatcher routes the call. This keeps the strategy layer deterministic and testable.

### Rate Limit Isolation
The hub owns the TwelveData budget (8 req/min on free tier). Agents fetch candles from the hub cache — never from TwelveData directly. This prevents multiple agents from exhausting the quota simultaneously.

### Audit Trail
Every LLM decision and trade event is hashed and emitted on HashKey Chain via `DecisionLogger` and `TradeLogger`. The full reasoning text is stored off-chain in PostgreSQL and linked via `keccak256` hash. Immutable provenance, private content.

### Async First
FastAPI + SQLAlchemy async + asyncpg throughout. The trading loop is a single async task. On-chain tx submission runs in `run_in_executor()` to avoid blocking the event loop.

### Multi-Tenant Security
All database queries in the hub filter by `user_id`. The `onlyOwner` modifier in both Solidity contracts ensures only the deployer key can emit events.

---

## Quick Facts

| Metric | Value |
|--------|-------|
| Python version | 3.12 |
| Node.js framework | Next.js 15 |
| Database | PostgreSQL (async) |
| Database tables | 8 |
| Trading strategies | 30+ |
| LLM providers supported | 4 (OpenAI, Anthropic, DeepSeek, Gemini) |
| Clients | 4 (TUI, CLI, Telegram, Web) |
| On-chain network | HashKey Chain (EVM) |
| Smart contracts | 2 (DecisionLogger, TradeLogger) |
| API endpoints (approx) | 50+ |
| Hub port | 9000 |
| Agent base port | 8000+ |

---

*Artic — transparent, LLM-orchestrated, on-chain verifiable.*
