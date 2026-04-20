# Data Model — Alpha

Two Postgres instances. Hub = shared tenant-wide state. Each user VM = own DB for that user's operational state. Alembic migrations **required from alpha start** (new policy, current repo has none).

## Hub Postgres

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| wallet_address | TEXT | e.g. `init1…` (bech32) or `0x…` (EVM); canonical lowercase |
| wallet_chain | TEXT | e.g. `initia-testnet`, `initia-mainnet`; matches `AUTH_SUPPORTED_CHAINS` |
| init_username | TEXT NULL | resolved `.init` name; NULL if unregistered |
| init_username_resolved_at | TIMESTAMP NULL | stale if > 24h; background refresh |
| api_key_hash | TEXT NULL | SHA-256 of raw key |
| created_at | TIMESTAMP | |
| UNIQUE(wallet_address, wallet_chain) | | same address on different chains = separate accounts (by design) |

No email / password — auth is wallet-signature only (see `auth_nonce`, `auth_session_keys`).

### auth_nonce
Short-lived challenge rows issued by `/auth/nonce` and consumed by `/auth/verify`. Single-use; 5-min TTL.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| address | TEXT | requesting wallet address |
| chain | TEXT | must be in `AUTH_SUPPORTED_CHAINS` |
| nonce | TEXT | 32 bytes URL-safe |
| expires_at | TIMESTAMP | `now() + AUTH_NONCE_TTL_SECONDS` |
| used_at | TIMESTAMP NULL | set when `/auth/verify` consumes |
| created_at | TIMESTAMP | |

Index: `(address, chain, used_at)` for lookup; periodic sweep deletes rows older than 1h.

### auth_session_keys
Ephemeral session keypairs authorized by the user's wallet at connect time. Dashboard holds the private half in memory; hub stores the public half + policy. Used to sign state-changing requests without re-prompting the wallet.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | exposed as `X-Session-Id` |
| user_id | UUID FK→users | |
| session_pub | TEXT | base64 of public key (curve depends on client) |
| scope | TEXT | alpha: single value `authenticated-actions`; beta splits |
| expires_at | TIMESTAMP | `now() + AUTH_SESSION_TTL_SECONDS` (default 8h) |
| last_nonce | BIGINT | monotonic counter; updated atomically on each request |
| revoked_at | TIMESTAMP NULL | set by `/auth/session DELETE` or by rotation |
| created_at | TIMESTAMP | |

Index: `(user_id, revoked_at)`.

### user_secrets
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| key_name | TEXT | e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY |
| encrypted_value | TEXT | AES-GCM ciphertext |
| updated_at | TIMESTAMP | |
| UNIQUE(user_id, key_name) | | |

### user_vms
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users UNIQUE | one VM per user |
| provider_vm_id | TEXT | Firecracker/Fly machine id |
| endpoint | TEXT | internal URL for mTLS proxy |
| status | TEXT | running / stopped / waking / draining / error |
| last_active_at | TIMESTAMP | updated on any client request through proxy |
| image_tag | TEXT | user-server image version (defer upgrade logic to beta) |
| wallet_address | TEXT | testnet chain wallet |

### credits
| Column | Type | Notes |
|--------|------|-------|
| user_id | UUID PK FK→users | |
| balance_ah | NUMERIC(18,6) | agent-hours remaining |
| updated_at | TIMESTAMP | |

### credit_ledger
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| delta_ah | NUMERIC(18,6) | positive=grant, negative=debit |
| reason | TEXT | tick_debit / admin_grant / halt_refund |
| agent_id | UUID NULL | for debits |
| created_at | TIMESTAMP | |

### marketplace_strategy
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| owner_id | UUID FK→users | |
| name | TEXT | |
| description | TEXT | |
| code_hash | TEXT | SHA-256 of Python source |
| code_blob | TEXT | source (RestrictedPython-safe) |
| installs | INT DEFAULT 0 | |
| reports | INT DEFAULT 0 | |
| status | TEXT | public / under_review / delisted |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### marketplace_report
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| strategy_id | UUID FK→marketplace_strategy | |
| reporter_id | UUID FK→users | |
| reason | TEXT | |
| created_at | TIMESTAMP | |
| UNIQUE(strategy_id, reporter_id) | | |

### indexer_tx_mirror
Mirror of user-server local indexer; filled via pull sync every 30min + pre-drain flush.

| Column | Type | Notes |
|--------|------|-------|
| tx_hash | TEXT PK | |
| user_id | UUID FK→users | |
| agent_id | UUID | (user-scoped, not FK'd to hub) |
| kind | TEXT | trades / supervise |
| amount_usdt | NUMERIC NULL | null for supervise |
| block_number | BIGINT | |
| tags | JSONB NOT NULL | canonical keys below |
| created_at | TIMESTAMP | |

Indexes:
```sql
CREATE INDEX ON indexer_tx_mirror (user_id, created_at DESC);
CREATE INDEX ON indexer_tx_mirror (kind, amount_usdt DESC) WHERE amount_usdt IS NOT NULL;
CREATE INDEX ON indexer_tx_mirror USING GIN (tags);
```

### market_cache
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| symbol | TEXT | |
| timeframe | TEXT | 1m / 5m / 15m / 1h / 4h / 1d |
| candles | JSONB | OHLCV array |
| last_fetched | TIMESTAMP | |
| UNIQUE(symbol, timeframe) | | |

### otel_events
(Optional; otherwise ship to external OTel collector.)

## User-Server Postgres (one per user VM)

### agents
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | TEXT | |
| symbol | TEXT | |
| llm_provider | TEXT | openai / anthropic / deepseek / gemini |
| llm_model | TEXT | |
| strategy_pool | JSONB | allowed strategy ids (built-in + user-installed) |
| risk_params | JSONB | amount_usdt, leverage, tp_pct, sl_pct, poll_seconds, supervisor_interval |
| container_id | TEXT NULL | |
| port | INT NULL | |
| status | TEXT | stopped / starting / alive / stopping / error |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### trades
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| agent_id | UUID FK→agents | |
| side | TEXT | long / short |
| entry_price | NUMERIC | |
| exit_price | NUMERIC NULL | |
| size_usdt | NUMERIC | |
| leverage | INT | |
| pnl_usdt | NUMERIC NULL | |
| strategy | TEXT | |
| open_at | TIMESTAMP | |
| close_at | TIMESTAMP NULL | |
| close_reason | TEXT | TP / SL / SUPERVISOR / MANUAL |
| tx_hash | TEXT NULL | set after on-chain log |

### log_entries
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| agent_id | UUID FK→agents | |
| level | TEXT | init / llm / tick / action / sl_tp / supervisor / error / warn |
| message | TEXT | |
| ts | TIMESTAMP | |

Append-only. Bulk-insert every 10 ticks.

### strategies
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| source | TEXT | builtin / marketplace / authored |
| name | TEXT | |
| code_hash | TEXT NULL | null for builtin |
| code_blob | TEXT NULL | |
| marketplace_id | UUID NULL | for traceability |
| installed_at | TIMESTAMP | |

### indexer_tx (local)
Same schema as `indexer_tx_mirror` except scoped to this user's agents. Written on every successful chain tx. Pushed to hub in batches.

## Canonical `tags` keys (both sides agree)

```json
{
  "strategy_id": "ema_crossover",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-6",
  "symbol": "BTCUSDT",
  "side": "long",
  "pnl_bps": 42
}
```

Extra keys allowed but not indexed. `amount_usdt` is a real column, **not** a tag.

## Rules

- Every hub query on per-user tables filters `WHERE user_id = current_user.id`
- `encrypted_value` never logged, never returned to client
- `log_entries` and `credit_ledger` are append-only
- `indexer_tx_mirror` is a mirror — truth lives on-chain + in user-server local table
- Alembic migrations mandatory; drop `init_db.create_all` from hub startup path
