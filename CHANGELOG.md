# Changelog

All notable changes to Artic are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### In Progress
- HashKey Global live executor (`app/executor/hashkey.py`)
- On-chain `onchain_trades` DB table integration
- Litepaper page

---

## [0.3.0] — 2026-04-15

### Added
- **Smart contracts deployed to HashKey Chain testnet**
  - `DecisionLogger` at `0x70a15Db526104abC2f021b7c690cd89a07EDE49C` (block 26543461)
  - `TradeLogger` at `0xeeb56334152D6bDB62aacF56f8DbCceA5210b78D` (block 26543465)
- `app/onchain_logger.py` — async keccak256-based decision logging to HashKey Chain
- `app/onchain_trade_logger.py` — trade open/close event logging with `1e8` price scaling
- `hub/db/models/onchain.py` — `onchain_decisions` and `onchain_trades` ORM tables
- `contracts/deploy.py` and `contracts/deploy_trade_logger.py` — Python deployment scripts using `web3` + `py-solc-x`
- Open source contribution infrastructure: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, GitHub templates, CI workflow

### Changed
- `README.md` rewritten as comprehensive project reference (architecture, full module map, contract addresses, DB schema, auth flows)

---

## [0.2.0] — 2026-04-01

### Added
- **Web client** (`clients/web/`) — Next.js 15 landing page + MDX documentation site
  - 10 documentation pages covering architecture, auth, strategies, CLI, deployment, hub API
  - Dark-only design system with CSS custom properties
  - shadcn/ui component library integration
- **Vercel deployment** configuration for web client
- `clients/web/app/blog/` — blog section
- `clients/web/app/jobs/` — careers page
- `clients/web/app/litepaper/` — litepaper page
- `lib/docs-nav.ts` — sidebar navigation structure

### Fixed
- Vercel deployment environment variable handling
- Next.js layout metadata configuration

---

## [0.1.0] — 2026-03-15

### Added
- **Hub orchestrator** (`hub/`) — FastAPI central server on port 9000
  - JWT + API key authentication
  - Agent lifecycle management via Docker SDK
  - Thread-safe atomic port allocation (`hub/docker/ports.py`)
  - PostgreSQL async ORM (SQLAlchemy + asyncpg), 8 tables
  - APScheduler-based TwelveData candle cache (60s refresh)
  - WebSocket broadcaster for real-time agent status
  - `/internal` push endpoints for agent → hub communication
  - AES-encrypted user and agent secret storage
  - Alembic migrations
- **Trading engine** (`app/`) — FastAPI agent container on port 8000+
  - Main trading loop (`engine.py`)
  - Pyth Hermes live price feeds (27 crypto symbols)
  - TwelveData OHLCV via hub cache
  - LLM strategy planner (`llm/llm_planner.py`) — OpenAI, Anthropic, DeepSeek, Gemini
  - Paper trading executor (`executor/paper.py`)
  - Circular log buffer (1000 entries)
  - Hub callback push (status, trades, logs)
- **30+ quant strategies** (`app/strategies/`)
  - 8 momentum algorithms
  - 6 mean-reversion algorithms
  - 3 volatility algorithms
  - 3 volume algorithms
  - 2 statistical algorithms
  - Kelly criterion + volatility scaling risk sizing
  - Session and day-of-week time filters
- **TUI client** (`clients/tui/`) — Textual-based terminal UI, 5 screens
- **CLI client** (`clients/cli/`) — argparse CLI with `--json` output
- **Telegram bot** (`clients/telegram/`) — python-telegram-bot 20+
- **Hub Python SDK** (`hub/client.py`) — shared by all clients
- **Docker Compose** stack — hub service + `artic-net` bridge network
- **pytest test suite** across hub, app, strategies, and clients

---

[Unreleased]: https://github.com/silonelabs/artic/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/silonelabs/artic/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/silonelabs/artic/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/silonelabs/artic/releases/tag/v0.1.0
