# API Contracts — Alpha

Three surfaces: **Hub public**, **Hub↔User-Server internal**, **User-Server↔Agent internal**. Every path that requires auth notes the header.

## Hub public API (client-facing)

All routes prefixed `/api/v1`. Auth: JWT in `Authorization: Bearer …` unless noted.

### Auth

Wallet-signature flow. Two-step: fetch nonce, sign canonical message (wallet + delegated session key in one sig), post back to verify. InterwovenKit handles the wallet side on the client.

| Method | Path | Auth | Body / Returns |
|--------|------|------|----------------|
| POST | `/auth/nonce` | — | `{address, chain}` → `{nonce, message, expires_at}` |
| POST | `/auth/verify` | — | `{address, chain, nonce, signature, pubkey, session_pub, session_scope, session_expires_at}` → `{access_token, session_id, init_username}` + Set-Cookie: refresh_token (httpOnly) |
| POST | `/auth/refresh` | refresh cookie | → `{access_token}` |
| GET | `/auth/me` | JWT | → `{id, wallet_address, wallet_chain, init_username, credits, vm_status}` |
| GET | `/auth/session` | JWT | → list of user's active session keys |
| DELETE | `/auth/session` | JWT + session headers | revoke current session + clear refresh cookie |

**Canonical sign-in message** (server builds, client signs verbatim):

```
artic.trade wants you to sign in with your {chain} account:
{address}

Session public key: {session_pub}
Scope: {session_scope}
Nonce: {nonce}
Issued At: {issued_at_iso}
Expires At: {session_expires_at_iso}
```

**Session-key headers on state-changing requests** (POST/PATCH/DELETE):

| Header | Meaning |
|--------|---------|
| `Authorization: Bearer <jwt>` | identity |
| `X-Session-Id` | the `session_id` from `/auth/verify` |
| `X-Session-Nonce` | monotonic integer; must exceed stored `last_nonce` for the session |
| `X-Session-Sig` | base64 signature by `session_priv` over `json({method, path, body_sha256, session_id, nonce}, sort_keys=True)` |

Missing session headers on a state-changing endpoint → `AUTH_REQUIRED` (401). Read endpoints (GET) require only the JWT.

### Credits

| Method | Path | Returns |
|--------|------|---------|
| GET | `/credits` | `{balance_ah, last_debit_at}` |
| GET | `/credits/ledger?limit=100` | list of ledger rows |

### User-scoped proxy (main API surface — routed to user-server)

All `/api/v1/u/*` calls are transparently proxied by hub to the caller's user-server. Hub triggers cold-wake if the VM is stopped.

| Method | Path | Proxied to user-server path | Purpose |
|--------|------|----------------------------|---------|
| GET | `/u/agents` | `/agents` | list user's agents |
| POST | `/u/agents` | `/agents` | create |
| GET | `/u/agents/{id}` | `/agents/{id}` | detail |
| PATCH | `/u/agents/{id}` | `/agents/{id}` | update config |
| DELETE | `/u/agents/{id}` | `/agents/{id}` | delete |
| POST | `/u/agents/{id}/start` | `/agents/{id}/start` | start tick loop |
| POST | `/u/agents/{id}/stop` | `/agents/{id}/stop` | stop tick loop |
| GET | `/u/agents/{id}/status` | `/agents/{id}/status` | current state |
| GET | `/u/agents/{id}/logs?limit=200` | `/agents/{id}/logs` | recent logs |
| GET | `/u/agents/{id}/trades` | `/agents/{id}/trades` | trade history |
| POST | `/u/agents/start-all` | `/agents/start-all` | group start |
| POST | `/u/agents/stop-all` | `/agents/stop-all` | group stop (also used on kill-switch) |
| GET | `/u/strategies` | `/strategies` | installed + built-in |
| POST | `/u/strategies` | `/strategies` | upload own |
| DELETE | `/u/strategies/{id}` | `/strategies/{id}` | remove |

### Marketplace

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/marketplace?sort=installs&limit=50` | list public strategies |
| GET | `/marketplace/{id}` | detail (incl. code) |
| POST | `/marketplace` | publish (code blob + metadata) |
| POST | `/marketplace/{id}/install` | copy into caller's user-server |
| POST | `/marketplace/{id}/report` | `{reason}` — one report per user per strategy |
| POST | `/admin/marketplace/{id}/delist` | admin only |

### Market data

| Method | Path | Returns |
|--------|------|---------|
| GET | `/market/price/{symbol}` | `{price, ts, source}` (Pyth) |
| GET | `/market/candles?symbol=&timeframe=&limit=` | OHLCV from cache |

### Indexer (read across all users)

| Method | Path | Returns |
|--------|------|---------|
| GET | `/indexer/tx?user_id=&agent_id=&kind=&min_amount=&limit=` | mirrored tx rows |
| GET | `/indexer/tx/{hash}` | single row |

### WebSocket

| Path | Stream |
|------|--------|
| `/ws/u/agents/{id}/status` | proxied from user-server; status ticks |
| `/ws/u/agents/{id}/logs` | proxied from user-server; log lines |
| `/ws/prices` | Pyth broadcast |

## Hub ↔ User-Server internal API

Auth: mTLS + `X-Hub-Secret` (hub→user-server) or `X-UserServer-Token` (user-server→hub). Never exposed to clients.

### Hub → User-Server (on top of proxied client calls above)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | liveness for hub wake poll |
| POST | `/hub/drain` | flush + halt everything, prepare for snapshot |
| POST | `/hub/halt` | stop all agents (credits depleted) |
| POST | `/hub/secrets/refresh` | re-inject decrypted user secrets (post-wake) |
| GET | `/hub/indexer/since?ts=` | return new indexer_tx rows since ts |

### User-Server → Hub

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/internal/v1/indexer/flush` | push batched indexer_tx rows |
| POST | `/internal/v1/credits/heartbeat` | report `alive_agents` count (hub is authority, this is reconciliation only) |
| POST | `/internal/v1/otel/spans` | OTel trace export (or direct collector) |

## User-Server ↔ Agent API

Auth: `X-Internal-Secret` header (shared secret, injected at spawn). Network: VM-internal only.

### User-Server → Agent

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | spawn-time readiness |
| POST | `/start` | begin tick loop with `StartRequest` body |
| POST | `/stop` | graceful stop |
| GET | `/status` | current position, price, strategy, PnL |
| GET | `/logs?limit=` | ring-buffer tail |

### Agent → User-Server

| Method | Path | Frequency |
|--------|------|-----------|
| POST | `/agents/{id}/status` | every tick |
| POST | `/trades` | on open/close |
| POST | `/logs` | every 10 ticks (batched) |
| POST | `/supervisor` | supervisor decision events |
| POST | `/signal-request` | request LLM/strategy dispatch (proxy path, see below) |

## LLM proxy (user-server internal)

Agent never holds LLM keys. Agent calls user-server:

| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | `/llm/plan` | `{symbol, regime, candles}` | `{strategy, lookback, threshold, …}` |
| POST | `/llm/supervise` | `{position, context}` | `{action: KEEP/CLOSE/ADJUST, params}` |
| POST | `/llm/chat` | `{messages, model}` | `{reply}` |

User-server picks provider/model per agent, injects the user's key from in-memory cache.

## Error shape (all APIs)

```json
{
  "error": {
    "code": "CREDITS_DEPLETED",
    "message": "Account balance exhausted",
    "details": { "balance_ah": 0 }
  }
}
```

Standard codes: `AUTH_REQUIRED`, `AUTH_INVALID`, `CREDITS_DEPLETED`, `VM_WAKING`, `VM_UNAVAILABLE`, `RATE_LIMITED`, `NOT_FOUND`, `VALIDATION`, `INTERNAL`.

## Versioning

All public APIs under `/api/v1`. Bump only on breaking change. Additive fields don't require version bump.
