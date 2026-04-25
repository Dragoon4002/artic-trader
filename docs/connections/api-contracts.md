# API Contracts — Hub (canonical)

> Source of truth for request/response shapes the **hub** exchanges with clients and internal services.
> Update this file **before** changing any endpoint or adding a new one.
> Code mirror: [clients/web/lib/schemas/](../../clients/web/lib/schemas/) (zod + inferred types).

Scope rule: this doc lists only endpoints the hub currently serves (including proxy pass-throughs to user-server that present the hub as the contract boundary). Pending endpoints — credits, ledger, indexer, marketplace — are tracked at the bottom under [Pending / not yet served](#pending--not-yet-served) and kept in [schemas/pending.ts](../../clients/web/lib/schemas/pending.ts).

## Quick index

| Domain | Schema file | Auth surface |
|--------|-------------|-------------|
| Auth | `schemas/auth.ts` | public → JWT → session-key |
| Agents (+ trades + logs) | `schemas/agents.ts` | JWT (read), session-key (write), via `/u/*` proxy |
| Strategies | `schemas/strategies.ts` | JWT + session-key, via `/u/*` proxy |
| Market | `schemas/market.ts` | public |
| Secrets | `schemas/secrets.ts` | JWT |
| Health | `schemas/health.ts` | public |
| WebSocket | `schemas/ws.ts` | public today; proxied `/ws/u/*` returns 1011 until user-server lands |
| Internal (user-server → hub, images admin) | `schemas/internal.ts` | `X-UserServer-Token` / `X-Hub-Secret` |
| Errors | `schemas/errors.ts` | — (returned on every non-2xx) |

---

## Auth

Wallet-signature flow. Two-step: fetch nonce, sign canonical message (wallet + delegated session key in one sig), post back to verify. `@source hub/auth/router.py`.

| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/auth/nonce` | — | `NonceRequest` | `NonceResponse` |
| POST | `/auth/verify` | — | `VerifyRequest` | `VerifyResponse` + Set-Cookie `refresh_token` (httpOnly) |
| POST | `/auth/refresh` | refresh cookie | — | `TokenResponse` |
| GET | `/auth/me` | JWT | — | `MeResponse` |
| GET | `/auth/session` | JWT | — | `SessionInfo[]` |
| DELETE | `/auth/session` | JWT + session headers | — | `RevokeSessionResponse` |
| POST | `/api/keys` | session-key | — | `ApiKeyResponse` (one-time plaintext) |

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

**Session-key headers** (required on every POST/PATCH/DELETE):

| Header | Meaning |
|--------|---------|
| `Authorization: Bearer <jwt>` | identity |
| `X-Session-Id` | `session_id` from `/auth/verify` |
| `X-Session-Nonce` | monotonic integer; must exceed stored `last_nonce` |
| `X-Session-Sig` | base64 signature by `session_priv` over `json({method, path, body_sha256, session_id, nonce}, sort_keys=True)` |

Missing session headers on state-changing endpoint → `AUTH_REQUIRED` (401). Read endpoints need only the JWT.

---

## Agents (via `/u/*` proxy)

Hub transparently proxies `/api/v1/u/*` to the caller's user-server. Cold-wake triggered if VM is stopped. Payload shapes are pinned against the hub as the contract boundary.

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/u/agents` | — | `Agent[]` |
| POST | `/u/agents` | `CreateAgentRequest` | `Agent` |
| GET | `/u/agents/{id}` | — | `Agent` |
| PATCH | `/u/agents/{id}` | `UpdateAgentRequest` | `Agent` |
| DELETE | `/u/agents/{id}` | — | `AgentLifecycleResponse` |
| POST | `/u/agents/{id}/start` | — | `AgentLifecycleResponse` |
| POST | `/u/agents/{id}/stop` | — | `AgentLifecycleResponse` |
| GET | `/u/agents/{id}/status` | — | `Agent` |
| GET | `/u/agents/{id}/logs?limit=` | — | `LogEntry[]` |
| GET | `/u/agents/{id}/trades` | — | `Trade[]` |
| POST | `/u/agents/start-all` | — | `AgentLifecycleResponse` |
| POST | `/u/agents/stop-all` | — | `AgentLifecycleResponse` |

**Enums** (web-side superset; hub will align):

- `AgentStatus`: `"alive" | "stopped" | "starting" | "error" | "halted"`
- `Side`: `"long" | "short" | "flat"`
- `CloseReason`: `"TP" | "SL" | "SUPERVISOR" | "MANUAL"`
- `LogLevel`: `"init" | "llm" | "tick" | "action" | "sl_tp" | "supervisor" | "warn" | "error"`

---

## Strategies (via `/u/*` proxy)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/u/strategies` | — | `StrategyListResponse` |
| POST | `/u/strategies` | `CreateStrategyRequest` | `Strategy` |
| DELETE | `/u/strategies/{id}` | — | `DeleteStrategyResponse` |

`StrategySource`: `"builtin" | "marketplace" | "authored"`.

---

## Market

Public. No auth. `@source hub/market/router.py`.

| Method | Path | Query | Response |
|--------|------|-------|----------|
| GET | `/api/market/price/{symbol}` | — | `PriceResponse` |
| GET | `/api/market/prices` | — | `PricesResponse` (dict by symbol) |
| GET | `/api/market/candles` | `symbol` (req), `interval="15m"` | `CandlesResponse` |

`Candle` shape comes from TwelveData: `{ datetime, open, high, low, close, volume }` — `datetime` format `"YYYY-MM-DD HH:MM:SS"`.

---

## Secrets

Write-only. Plaintext over TLS; hub encrypts AES-GCM before storing. List returns key names only — never plaintext or ciphertext. `@source hub/secrets/service.py`.

| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/api/v1/secrets` | JWT | `SecretWrite` | `SecretPutResponse` |
| GET | `/api/v1/secrets` | JWT | — | `SecretsListResponse` |
| DELETE | `/api/v1/secrets/{key_name}` | JWT | — | `SecretDeleteResponse` |

---

## Health

| Method | Path | Response |
|--------|------|----------|
| GET | `/health` | `HealthResponse` |
| GET | `/health/ready` | `ReadyResponse` |

---

## WebSocket

All messages follow `{ type, data }` envelope (`WsEnvelope`).

| Path | Auth | Message type | Notes |
|------|------|--------------|-------|
| `/ws/prices` | — | `WsPricesMessage` | Pyth broadcast, 2s poll |
| `/ws/agents/{id}/status` | container-internal | `WsAgentStatusMessage` | Not client-facing |
| `/ws/agents/{id}/logs` | container-internal | `WsAgentLogsMessage` | Not client-facing |
| `/ws/u/agents/{id}/status` | JWT (alpha) | `WsAgentStatusMessage` | Proxied — returns 1011 until user-server lands |
| `/ws/u/agents/{id}/logs` | JWT (alpha) | `WsAgentLogsMessage` | Proxied — returns 1011 until user-server lands |

---

## Internal (never called from browser)

### User-server → hub (`X-UserServer-Token`)

All Phase-4 stubs today; response is `InternalNoopResponse` with `ok: true`.

| Method | Path | Request | Purpose |
|--------|------|---------|---------|
| POST | `/internal/v1/credits/heartbeat` | `CreditsHeartbeatRequest` | Alive-agent count reconciliation |
| POST | `/internal/v1/indexer/flush` | `IndexerFlushRequest` | Push batched on-chain rows pre-drain |
| POST | `/internal/v1/otel/spans` | `OtelSpansRequest` | OTel trace export |

### Admin image fetch (`X-Hub-Secret`)

| Method | Path | Response |
|--------|------|----------|
| GET | `/internal/v1/images` | `ImageListResponse` |
| GET | `/internal/v1/images/{name}` | `application/gzip` tarball (not JSON) |

Whitelist: `artic-agent-v0.tar.gz`, `artic-user-server-v0.tar.gz`.

### Agent → user-server (for reference)

Future user-server surface. Shapes live with that service when it ships; intentionally not mirrored here to avoid drift.

| Method | Path | Frequency |
|--------|------|-----------|
| POST | `/agents/{id}/status` | every tick |
| POST | `/trades` | on open/close |
| POST | `/logs` | every 10 ticks (batched) |
| POST | `/supervisor` | decision events |
| POST | `/signal-request` | LLM proxy dispatch |

---

## Error envelope

Every non-2xx response (from any endpoint, including internal) returns:

```json
{
  "error": {
    "code": "CREDITS_DEPLETED",
    "message": "Account balance exhausted",
    "request_id": "",
    "details": { "balance_ah": 0 }
  }
}
```

`code` vocabulary (`schemas/errors.ts → KnownErrorCode`):

- HTTP-derived: `BAD_REQUEST`, `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, `RATE_LIMITED`, `INTERNAL_ERROR`, `UPSTREAM_ERROR`, `UNAVAILABLE`, `ERROR`
- Hub-custom: `AUTH_REQUIRED`, `AUTH_INVALID`, `CREDITS_DEPLETED`, `VM_WAKING`, `VM_UNAVAILABLE`

Parsers treat `code` as open-string — unknown codes from future branches won't throw.

---

## Pending / not yet served

Drafted against `docs/alpha/api-contracts.md`. Demo pages consume these via `lib/demo-data.ts` → `lib/api.ts` casts. Promote a schema out of `schemas/pending.ts` into its canonical module when the backing endpoint ships.

| Domain | Endpoints (alpha target) | Schemas |
|--------|-------------------------|---------|
| Credits | `GET /credits`, `GET /credits/ledger` | `Credits`, `LedgerRow` |
| Indexer | `GET /indexer/tx`, `GET /indexer/tx/{hash}` | `IndexerRow`, `IndexerFilter` |
| Marketplace | `GET /marketplace`, `GET /marketplace/{id}`, `POST /marketplace`, `POST /marketplace/{id}/install`, `POST /marketplace/{id}/report`, `POST /admin/marketplace/{id}/delist` | `MarketplaceItem`, `MarketplaceSort`, `MarketplaceReportRequest` |

---

## Versioning

All public APIs mount under `/api/v1`. Bump only on breaking change. Additive fields don't require a version bump. Zod schemas allow unknown fields (zod's default); clients forward-compatible.

## Maintenance rules

- Add/change an endpoint → edit the matching `schemas/*.ts` first, then this doc, then the hub route.
- Promoting from `pending.ts` → move schema to its canonical file and delete the pending row + pending table entry here.
- Every schema must carry an `@source <hub-path>` comment.
- Error codes added to `hub/utils/errors.py` must be mirrored in `KnownErrorCode`.
