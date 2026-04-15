# Artic

AI-powered multi-agent trading platform. An LLM selects from 30+ quant strategies and manages risk dynamically. A central hub orchestrates multiple isolated agent processes, each trading a different symbol.

**Architecture decisions & build plan**: `/.claude/plans/stateless-gliding-corbato.md`

## Module Map

| Module | Code | Module Guide | Docs | Tests |
|--------|------|-------------|------|-------|
| Hub (orchestrator) | `/hub/` | `/hub/CLAUDE.md` | `/docs/hub/` | `/tests/hub/` |
| App (trading engine) | `/app/` | `/app/CLAUDE.md` | `/docs/app/` | `/tests/app/` |
| Strategies (algos) | `/app/strategies/` | `/app/strategies/CLAUDE.md` | `/docs/strategies/` | `/tests/app/strategies/` |
| TUI client | `/clients/tui/` | `/clients/tui/CLAUDE.md` | `/docs/clients/tui/` | `/tests/clients/tui/` |
| CLI client | `/clients/cli/` | `/clients/cli/CLAUDE.md` | `/docs/clients/cli/` | `/tests/clients/cli/` |
| Telegram client | `/clients/telegram/` | `/clients/telegram/CLAUDE.md` | `/docs/clients/telegram/` | `/tests/clients/telegram/` |
| Web (landing+docs) | `/clients/web/` | `/clients/web/CLAUDE.md` | — | — |

## Cross-Module Concerns

- **Service boundaries & protocols**: `/docs/connections/service-map.md`
- **Auth flow**: `/docs/connections/auth-flow.md`
- **Env & secrets**: `/docs/connections/env-secrets.md`
- **System topology & data flow**: `/docs/architecture/overview.md`
- **Data model**: `/docs/architecture/data-model.md`

Full docs index: `/docs/CLAUDE.md` | Tests index: `/tests/CLAUDE.md`

## When to Read More

| Task | Load Module Guide | Load Docs |
|------|-------------------|-----------|
| Adding a strategy | `/app/strategies/CLAUDE.md` | `/docs/strategies/` |
| Changing an endpoint | `/app/CLAUDE.md` or `/hub/CLAUDE.md` | `/docs/connections/service-map.md` |
| Modifying auth | `/hub/CLAUDE.md` | `/docs/connections/auth-flow.md` |
| Adding a new client | relevant `/clients/*/CLAUDE.md` | `/docs/connections/service-map.md` |
| Changing DB schema | `/hub/CLAUDE.md` | `/docs/architecture/data-model.md` |
| Managing secrets/env | `/hub/CLAUDE.md` | `/docs/connections/env-secrets.md` |
| Agent lifecycle | `/hub/CLAUDE.md`, `/app/CLAUDE.md` | `/docs/architecture/overview.md` |
| Writing tests | relevant module CLAUDE.md | `/tests/CLAUDE.md` |
| Updating landing/docs | `/clients/web/CLAUDE.md` | — |

## Doc Maintenance Rules

- Update `/docs/connections/service-map.md` **before** adding a new call path
- Update `/docs/architecture/data-model.md` on any schema change
- Module CLAUDE.md files must stay under 50 lines
- Never duplicate info across files — use pointers
