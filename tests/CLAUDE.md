# Tests Index — Artic

Load this file when writing or modifying tests.

## Test Folders

| Folder | Tests For | Module Guide |
|--------|-----------|-------------|
| `/tests/hub/` | Auth, agent lifecycle, WebSocket, secrets, market cache | `/hub/CLAUDE.md` |
| `/tests/app/` | Engine loop, market data, LLM planner, executors | `/app/CLAUDE.md` |
| `/tests/app/strategies/` | Quant algorithms, signal dispatcher, risk sizing | `/app/strategies/CLAUDE.md` |
| `/tests/app/pyth_api_connection/` | Pyth Hermes integration tests | `/app/CLAUDE.md` |
| `/tests/clients/tui/` | TUI screens, HubClient integration | `/clients/tui/CLAUDE.md` |
| `/tests/clients/cli/` | CLI commands, --json output | `/clients/cli/CLAUDE.md` |
| `/tests/clients/telegram/` | Bot handlers, message formatting | `/clients/telegram/CLAUDE.md` |

## Conventions

- Test files mirror source: `engine.py` → `test_engine.py`
- `pytest` as test runner
- Mock external services (Pyth, TwelveData, LLM) — no real API calls
- Mock Docker for hub agent lifecycle tests
- Strategy tests verify `(signal: float, detail: str)` contract
- Strategy tests pass candle arrays only — never mock live prices
- Hub tests verify JWT + API key auth flows
- Never assert on plaintext API keys in fixtures — use dummy ciphertext
- All agent queries in hub tests must be user-scoped

## Related Docs

- Service boundaries (mock boundaries): `/docs/connections/service-map.md`
- Algorithm contract: `/app/strategies/CLAUDE.md`
