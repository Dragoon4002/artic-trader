# Contributing to Artic

Thanks for your interest. Artic is an AI-powered multi-agent trading platform — contributions are welcome across the stack: quant strategies, hub/app backend, clients (TUI/CLI/Telegram), smart contracts, and documentation.

---

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Types of Contributions](#types-of-contributions)
5. [Adding a New Strategy](#adding-a-new-strategy)
6. [Workflow](#workflow)
7. [Code Standards](#code-standards)
8. [Testing](#testing)
9. [Commit & PR Conventions](#commit--pr-conventions)
10. [What Not to Contribute](#what-not-to-contribute)

---

## Before You Start

- Check [open issues](../../issues) before starting work — someone may already be on it.
- For large changes (new modules, architectural shifts), open an issue first and discuss the approach before writing code.
- For small fixes (typos, bugs, minor improvements) just open a PR directly.

---

## Development Setup

### Prerequisites

- Python 3.12+
- Docker + Docker Compose
- PostgreSQL 15+ (or a free [Neon](https://neon.tech) instance)
- Node.js 20+ (only if touching the web client)

### 1. Fork and clone

```bash
git clone https://github.com/<your-fork>/hashkey.git
cd hashkey
```

### 2. Python environment

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx  # test dependencies
```

### 3. Environment variables

```bash
cp .env.example .env
# Fill in at minimum:
#   DATABASE_URL       — PostgreSQL connection string
#   INTERNAL_SECRET    — any random 40+ char string
#   JWT_SECRET         — any random 40+ char string
#   TWELVE_DATA_API_KEY — free tier at twelvedata.com
#   GEMINI_API_KEY     — or any other LLM provider key
```

### 4. Database

```bash
alembic upgrade head
```

### 5. Docker network + agent image

```bash
bash scripts/setup-network.sh
bash scripts/build-app-image.sh
```

### 6. Run hub locally

```bash
python -m hub.server
# Hub available at http://localhost:9000
```

### 7. Web client (optional)

```bash
cd clients/web
npm install
npm run dev
```

---

## Project Structure

```
hub/          Central orchestrator (FastAPI + PostgreSQL)
app/          Trading engine (one Docker container per symbol)
app/strategies/   30+ quant algorithms
clients/tui/  Terminal UI (Textual)
clients/cli/  CLI tool
clients/telegram/ Telegram bot
clients/web/  Next.js landing + docs
contracts/    Solidity contracts (HashKey Chain)
docs/         Architecture docs
tests/        pytest test suite
```

See [README.md](README.md) for the full module breakdown.

---

## Types of Contributions

| Type | Where | Notes |
|------|-------|-------|
| New quant strategy | `app/strategies/quant_algos/` | See dedicated section below |
| Bug fix | Anywhere | Include a regression test |
| Hub endpoint | `hub/` | Update `docs/connections/service-map.md` |
| New client command | `clients/*/` | Mirror hub SDK method 1:1 |
| Documentation | `docs/` or `clients/web/app/docs/` | MDX for web, Markdown for docs/ |
| On-chain logging | `contracts/`, `app/onchain_logger.py` | Coordinate via issue first |
| Test coverage | `tests/` | Always welcome |
| Performance | Anywhere | Profile first, share flamegraph in PR |

---

## Adding a New Strategy

This is the most common contribution. All strategies live in `app/strategies/quant_algos/` and must follow the same contract:

```python
def my_strategy(candles: list[dict], params: dict) -> tuple[float, str]:
    """
    Args:
        candles: OHLCV dicts sorted oldest → newest
                 keys: open, high, low, close, volume, timestamp
        params:  dict of strategy-specific parameters (can be empty {})

    Returns:
        signal: float in [-1.0, 1.0]
                -1.0 = strong short
                 0.0 = flat / no signal
                +1.0 = strong long
        detail: human-readable explanation string for the LLM
    """
```

**Rules:**
- Accept only `candles` and `params` — never fetch live prices inside a strategy.
- Return `(0.0, "insufficient data")` when candle history is too short.
- Add the function to the appropriate `*_algos.py` file (or create a new one for a new category).
- Register it in `app/strategies/signals.py` dispatcher.
- Add it to the strategy index in `app/onchain_logger.py`.
- Write at least one test in `tests/app/strategies/`.

**Example test:**
```python
def test_my_strategy_long_signal():
    candles = [{"open": 100, "high": 110, "low": 95, "close": 108, "volume": 1000} for _ in range(50)]
    signal, detail = my_strategy(candles, {})
    assert -1.0 <= signal <= 1.0
    assert isinstance(detail, str) and len(detail) > 0
```

---

## Workflow

1. **Fork** the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/my-strategy-name
   # or
   git checkout -b fix/hub-auth-bug
   ```

2. **Make changes** — keep each PR focused on one thing.

3. **Run tests** before opening a PR:
   ```bash
   pytest tests/
   ```

4. **Open a PR** against `main`. Fill in the PR template.

5. A maintainer will review within a few days. Address feedback, then it gets merged.

---

## Code Standards

### Python

- **Formatter:** `black` (line length 100)
- **Linter:** `ruff`
- **Type hints:** required on all public functions
- **Async:** use `async def` for any I/O — never `time.sleep()` in async context
- Log levels used across the codebase: `init`, `llm`, `start`, `tick`, `action`, `sl_tp`, `stop`, `error`, `warn`, `supervisor`
- No print statements in library code — use the `LogBuffer` or Python `logging`

```bash
pip install black ruff
black .
ruff check .
```

### TypeScript / Next.js (web client)

- **Formatter:** Prettier (config in `clients/web/`)
- Dark-only design — no light theme additions
- Colors via CSS custom properties in `globals.css`, not hardcoded hex values
- shadcn/ui components only — no other UI library additions

```bash
cd clients/web
npm run lint
npm run format
```

### Solidity

- Solidity 0.8.20
- Follow existing `onlyOwner` pattern
- No state variables unless absolutely necessary (contracts are event-emitters)
- Include SPDX license identifier

---

## Testing

```bash
# All tests
pytest tests/

# Specific module
pytest tests/hub/
pytest tests/app/strategies/
pytest tests/clients/

# With coverage
pytest tests/ --cov=hub --cov=app --cov-report=term-missing
```

**Requirements for a passing PR:**
- All existing tests pass
- New code has tests (strategies: correctness + edge cases; endpoints: happy path + auth failure)
- No real API calls in tests — mock Pyth, TwelveData, LLM, Docker

---

## Commit & PR Conventions

### Commit messages

```
<type>: <short description>

Types: feat | fix | docs | test | refactor | chore | strategy
```

Examples:
```
feat: add kalman filter mean reversion strategy
fix: hub port allocator race condition under concurrent spawns
docs: update service-map with /internal/trades endpoint
test: add coverage for llm_planner fallback path
strategy: implement ichimoku cloud signal
```

### PR titles

Same format as commit messages. Keep under 72 characters.

### PR checklist (also in PR template)

- [ ] Tests pass locally (`pytest tests/`)
- [ ] New code has tests
- [ ] No secrets or API keys committed
- [ ] Docs updated if adding/changing an endpoint or module
- [ ] `docs/connections/service-map.md` updated if adding a new call path
- [ ] Strategy registered in `signals.py` if adding a new algorithm

---

## What Not to Contribute

- **Live executor implementations** (HashKey Global, Binance, etc.) — coordinate via issue first; these touch real funds
- **Hardcoded API keys or private keys** anywhere in the codebase
- **Breaking changes to the `(signal, detail)` strategy contract** without an issue + discussion
- **New Python dependencies** without a clear justification in the PR description
- **Light mode** for the web client — the design is intentionally dark-only
- **Modifications to deployed contract addresses** in `contracts/*.json` — these are production artifacts

---

## Questions?

Open a [GitHub Discussion](../../discussions) or file an issue with the `question` label.
