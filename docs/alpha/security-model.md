# Security Model — Alpha

Pragmatic cut for alpha. Not enterprise-grade; blocks casual misuse and contains blast radius.

## Threat model (alpha)

| Threat | In scope |
|--------|---------|
| Wallet signature phishing / malicious dapp reuse of nonce | yes |
| Stolen session key from client memory | yes (capped by 8h TTL + revoke on logout) |
| Credential theft from client JS | yes |
| User strategy code tries to exfiltrate secrets / crash user-server | yes |
| User A accessing user B's data through hub | yes |
| Compromised user-server reaching hub as admin | yes |
| DDoS on hub | partial (rate limits only) |
| Chain key theft (platform-custodied VM wallet) | yes (testnet → low stakes; beta hardens) |
| Supply-chain (image registry compromise) | out of scope alpha |
| Nation-state / persistent APT | out of scope |

## Auth

### Client → Hub — wallet connect + session key

- Identity: wallet signature over a server-issued nonce challenge + delegated session-key authorization (single popup). Auth is by `(wallet_address, wallet_chain)` keyed UPSERT; email/password entirely absent.
- Wallet stack: `@initia/interwovenkit-react` (locked; chain-specific verifier dispatched server-side).
- Nonce (`auth_nonce`): random 32 bytes URL-safe, single-use, 5-min TTL. Reuse rejected; replay-safe across tabs.
- Signature verifier: pluggable by chain (`VERIFIERS[chain]`). Alpha ships ADR-36 for Cosmos-style Initia addresses; EIP-191 slot-in when an EVM chain joins.
- Canonical sign-in message (see api-contracts.md): domain-bound to `artic.trade`; binds `address`, `chain`, `nonce`, `session_pub`, `scope`, `expires_at` — one signature authorizes both account access and the session key.
- Session (`auth_session_keys`): ephemeral keypair generated client-side in memory only; server stores only `session_pub` + scope + `expires_at` + `last_nonce`. TTL default 8h (`AUTH_SESSION_TTL_SECONDS`).
- State-changing requests carry `X-Session-Id`, monotonic `X-Session-Nonce`, `X-Session-Sig` over `json({method, path, body_sha256, session_id, nonce}, sort_keys=True)`. Hub rejects if nonce `<= last_nonce`, session expired, or sig invalid. `last_nonce` updated in same transaction to prevent replay.
- Read endpoints (GET) require JWT only.
- JWT: 15-min access token + rotating refresh token in httpOnly cookie. Refresh-token reuse detection revokes the family.
- Logout: `DELETE /auth/session` sets `revoked_at`, clears refresh cookie.
- Rate-limit: `/auth/nonce` 10/min per IP + address; `/auth/verify` 5/min per address.

### Hub ↔ User-Server

- mTLS between hub and every user-server (per-VM cert minted by hub CA at VM provision)
- Additionally `X-Hub-Secret` header for hub→user-server, `X-UserServer-Token` reverse
- Tokens rotate on every VM snapshot→wake cycle

### User-Server → Agent

- Shared `INTERNAL_SECRET` injected as env var at agent spawn, unique per user VM (rotated on every VM wake)
- Agent includes on every push; user-server rejects on mismatch
- VM-internal network only; no public exposure of agent port

## Secrets

### Resolution order (agent → what it uses)

1. Ephemeral at-spawn env (user-server decides per session)
2. User-server memory cache (loaded from hub at VM wake via `/hub/secrets/refresh`)
3. None → agent operates without (e.g., no LLM fallback; agent errors)

### Storage

- Hub Postgres `user_secrets.encrypted_value` = AES-GCM ciphertext
- KEK (encryption key) in hub process env, **never** in DB
- Decryption happens on hub only, pushed in-memory to user-server on wake
- User-server **never** writes decrypted secrets to disk

### Agent never sees user's LLM key

Previously injected into agent env. **Alpha change**: keys stop at user-server. Agent hits user-server `/llm/*` instead.

## Strategy sandbox

### RestrictedPython config

- Allowed imports: `math`, `statistics`, `numpy`, `talib` (curated whitelist)
- Allowed builtins: `abs, min, max, sum, len, range, enumerate, zip, map, filter, sorted, round, list, tuple, dict, set, bool, int, float, str`
- Disallowed: `open`, `__import__`, `eval`, `exec`, `compile`, `getattr`, `setattr`, `globals`, `locals`, `vars`, `object`, `type`, attribute access to `__*__`
- `_getattr_`, `_getitem_`, `_getiter_` hooked via RestrictedPython guards
- CPU: signal handler kills any strategy taking > 500ms per call
- Memory: RestrictedPython runs in same process but with per-call allocation tracker (soft limit 64MB, kill on breach)

### What a strategy can see

Input: `(plan: StrategyPlan, price_history: list[float], candles: list[dict])` — all plain values, no references to agent/user-server/hub objects.

Output: `(signal: float, detail: str)`. Any other return → rejected.

### What it cannot

- No network, no filesystem, no subprocess, no `os`, no `sys`
- No access to `user-server` secrets, keys, env
- Cannot crash the event loop — exceptions are caught, logged, and fall back to `simple_momentum`

## VM isolation

- One user VM per user. Zero lateral network path between user VMs.
- Hub is the only ingress/egress for user traffic.
- Platform ops SSH to user VMs is logged + alerted. No routine access.

## Chain key management

- Each user VM has its own testnet wallet (EOA)
- Private key encrypted with a per-VM KEK minted by hub CA, stored on VM disk, loaded into user-server memory on boot
- Platform funder wallet private key in hub env only; never leaves hub process
- Beta: migrate to user-owned wallets + MPC or KMS-backed signing

## Rate limits (hub)

| Scope | Limit |
|-------|------|
| Per IP | 60 req/min |
| Per user | 600 req/min |
| `/auth/nonce` per IP + address | 10 / min |
| `/auth/verify` per address | 5 / min |
| `/marketplace/publish` per user | 10/day |
| `/marketplace/report` per user | 20/day |
| WebSocket connections per user | 10 |

## Audit log (hub)

Append-only table `audit_log(user_id, action, target, metadata, ip, ua, ts)`.

Logged actions: auth events, secret writes, agent create/delete/start/stop, strategy publish/install/report, admin delist, credit grants.

## Observability

- OTel collector on hub; user-server + agents export spans, logs, metrics
- Dashboards: wake latency, tick rate, LLM call rate, chain tx success/fail, credit debit volume, sandbox violations, auth failures

## Known alpha gaps (accepted)

- No WAF
- No DDoS protection at edge
- No HSM for chain keys
- No formal pen-test
- No SOC2 / compliance cert
- Admin access uses shared credentials (fix before beta)
