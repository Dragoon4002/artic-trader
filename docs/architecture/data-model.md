# Data Model — Artic

PostgreSQL via SQLAlchemy async. Migrations via Alembic.

## Tables

### users

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | User identifier |
| email | TEXT UNIQUE | Login identity |
| password_hash | TEXT | Bcrypt hash |
| api_key_hash | TEXT NULL | SHA-256 hash of API key (for CLI/Telegram auth) |
| created_at | TIMESTAMP | Account creation time |

### agents

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Agent identifier |
| user_id | UUID FK→users | Owning user |
| symbol | TEXT | Trading pair (e.g. BTC/USD) |
| container_id | TEXT NULL | Docker container ID (null when stopped) |
| port | INTEGER NULL | Assigned port (null when stopped) |
| status | TEXT | alive / stopped / error |
| created_at | TIMESTAMP | Agent creation time |
| strategy_name | TEXT | Selected strategy (or "llm_auto") |
| interval_seconds | INTEGER | Trading loop tick interval |
| risk_params | JSONB | Stop-loss %, take-profit %, position size, leverage |
| live_mode | BOOLEAN | Must be false unless HashKey executor implemented |

### trades

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Trade identifier |
| agent_id | UUID FK→agents | Associated agent |
| side | TEXT | long / short |
| entry_price | NUMERIC | Position entry price |
| exit_price | NUMERIC NULL | Position exit price (null if open) |
| pnl | NUMERIC NULL | Realised PnL (null if open) |
| opened_at | TIMESTAMP | Position open time |
| closed_at | TIMESTAMP NULL | Position close time |

### log_entries

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Log identifier |
| agent_id | UUID FK→agents | Associated agent |
| level | TEXT | init/llm/start/tick/action/sl_tp/stop/error/warn/supervisor |
| message | TEXT | Log message |
| timestamp | TIMESTAMP | Log time |

> **Rule**: Bulk-inserted every 10 ticks from agent push. Append-only.

### market_cache

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Cache row identifier |
| symbol | TEXT | Trading pair |
| timeframe | TEXT | e.g. 15m, 1h, 1d |
| candles | JSONB | Array of OHLCV candle objects |
| last_fetched | TIMESTAMP | When TwelveData was last called |

> **Rule**: Serve stale if `last_fetched` < 60s ago. Hub APScheduler refreshes.

### user_secrets

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Row identifier |
| user_id | UUID FK→users | Owning user |
| key_name | TEXT | Secret key name |
| encrypted_value | TEXT | AES ciphertext — never plaintext |

### agent_secret_overrides

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Row identifier |
| agent_id | UUID FK→agents | Associated agent |
| key_name | TEXT | Secret key name |
| encrypted_value | TEXT | AES ciphertext — never plaintext |

### onchain_decisions

| Column | Type | Purpose |
|--------|------|---------|
| id | UUID PK | Row identifier |
| agent_id | UUID FK→agents | Associated agent |
| session_id | BYTEA | keccak256(symbol + agentId + timestamp) |
| tx_hash | TEXT | HashKey Chain transaction hash |
| block_number | BIGINT | Block number |
| reasoning_text | TEXT | Full LLM reasoning (off-chain storage) |
| created_at | TIMESTAMP | Decision time |

## Relationships

```
users 1──* agents (user_id)
agents 1──* trades (agent_id)
agents 1──* log_entries (agent_id)
users 1──* user_secrets (user_id)
agents 1──* agent_secret_overrides (agent_id)
agents 1──* onchain_decisions (agent_id)
```

## Rules

- All queries on `agents` must include `WHERE user_id = current_user.id`
- `encrypted_value` is AES ciphertext — never store plaintext API keys
- `log_entries` is append-only — bulk insert, never update
- Secret resolution: agent_secret_overrides → user_secrets → process .env
