# Project Brief — Artic

Reference doc for future sessions. Pointers, not duplication.

## What Artic is

AI-driven multi-agent trading platform. One LLM picks from 30+ quant strategies per symbol, a supervisor LLM revalidates each interval, and isolated Docker-per-symbol agents execute paper trades (live HashKey is WIP). Central hub owns auth, DB, market cache, WebSocket fan-out. Clients (TUI, CLI, Telegram, web) are thin — all state lives in hub Postgres.

## Module map

| Module | Path | Guide | Status |
|--------|------|-------|--------|
| Hub (orchestrator) | `/hub/` | [hub/CLAUDE.md](../hub/CLAUDE.md) | production-ready |
| App (trading engine) | `/app/` | [app/CLAUDE.md](../app/CLAUDE.md) | production-ready (paper) |
| Strategies | `/app/strategies/` | [app/strategies/CLAUDE.md](../app/strategies/CLAUDE.md) | 30+ algos, signals dispatcher |
| TUI | `/clients/tui/` | [clients/tui/CLAUDE.md](../clients/tui/CLAUDE.md) | Textual, hub-backed |
| CLI | `/clients/cli/` | [clients/cli/CLAUDE.md](../clients/cli/CLAUDE.md) | full commands |
| Telegram | `/clients/telegram/` | [clients/telegram/CLAUDE.md](../clients/telegram/CLAUDE.md) | wired, alerts |
| Web | `/clients/web/` | [clients/web/CLAUDE.md](../clients/web/CLAUDE.md) | marketing + MDX docs (no dashboard) |
| Contracts | `/contracts/` | — | DecisionLogger + TradeLogger deployed |

## Authoritative docs

- Architecture: [architecture/overview.md](architecture/overview.md)
- Data model: [architecture/data-model.md](architecture/data-model.md)
- Service map: [connections/service-map.md](connections/service-map.md)
- Auth flow: [connections/auth-flow.md](connections/auth-flow.md)
- Env & secrets: [connections/env-secrets.md](connections/env-secrets.md)
- **Current runtime flow + stubs**: [current-flow.md](current-flow.md)
- Docs index: [CLAUDE.md](CLAUDE.md)

## Stack

- Hub: Python 3.12, FastAPI, SQLAlchemy async, Postgres 16, APScheduler, Docker SDK
- App: Python 3.12, FastAPI, httpx, web3.py
- TUI: Textual · CLI: Typer · Telegram: python-telegram-bot · Web: Next.js 15, shadcn/ui, Tailwind v4, bun
- Chain: HashKey Chain (Solidity 0.8.x, ethers deploy scripts in `contracts/`)
- LLM providers: OpenAI, Anthropic, DeepSeek, Gemini (pluggable)

## Runtime invariants

- Agents are stateless across restart — Postgres is system of record
- Clients never reach agent containers directly — hub proxies everything
- One agent = one symbol
- Agent→hub is push-based via `/internal/*` (X-Internal-Secret)
- TwelveData rate budget owned by hub cache scheduler (agents never call it direct)
- Secrets never in plaintext at rest — AES in DB, ephemeral env at spawn

## Known open items (truth snapshot)

- HashKey live executor = skeleton (no REST calls yet)
- Alembic migrations dir empty — uses `create_all()`
- Tests ~zero — 1 TS pyth fetch only
- No web dashboard (agent control via TUI/CLI/Telegram)

## Doc rules (from root CLAUDE.md)

- Module CLAUDE.md under 50 lines
- Never duplicate — use pointers
- Update `connections/service-map.md` before any new call path
- Update `architecture/data-model.md` on any schema change

## Where Claude should start

| Task | Load first |
|------|-----------|
| New strategy | [app/strategies/CLAUDE.md](../app/strategies/CLAUDE.md) |
| New/changed endpoint | [connections/service-map.md](connections/service-map.md) + relevant module guide |
| Auth change | [connections/auth-flow.md](connections/auth-flow.md) |
| Schema change | [architecture/data-model.md](architecture/data-model.md) |
| Runtime debugging | [current-flow.md](current-flow.md) |
| New client | [connections/service-map.md](connections/service-map.md) + a sibling client guide |
| Live trading work | `/app/executor/hashkey.py` — expect stub |
