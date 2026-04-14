# Auth Flow — Artic

Two auth methods. Hub dependency `get_current_user` tries JWT first, then API key.

## JWT Auth (TUI, web dashboard)

1. Client sends `POST /auth/login` with email + password
2. Hub verifies bcrypt hash against `users.password_hash`
3. Hub issues JWT access token (15 min) + refresh token
4. Client includes `Authorization: Bearer <token>` on all `/api/*` requests
5. Refresh via `POST /auth/refresh` before expiry

| Token | Lifetime | Storage | Revocation |
|-------|----------|---------|-----------|
| Access (JWT) | 15 minutes | Client memory | Expires naturally |
| Refresh | Long-lived | Server-side | Server-side revocable |

## API Key Auth (CLI, Telegram bot)

1. User generates API key via `POST /api/keys`
2. Hub stores SHA-256 hash in `users.api_key_hash`, returns raw key once
3. Client includes `X-API-Key: <raw_key>` header on all requests
4. Hub hashes incoming key, compares against stored hash

> **Rule**: Raw API key shown only at creation. Lost key = regenerate.

## Internal Auth (agent → hub)

Agent containers authenticate to `/internal/*` endpoints with `X-Internal-Secret` header. Secret is injected as Docker env var at spawn, matches hub's `INTERNAL_SECRET` env var.

## Secrets Encryption

1. Client encrypts API keys with AES (key derived from user password or separate passphrase)
2. Ciphertext uploaded via `POST /api/secrets`
3. Hub stores ciphertext in `user_secrets` or `agent_secret_overrides`
4. At spawn: hub injects encrypted values as Docker env vars
5. Agent decrypts at runtime, or receives plaintext via ephemeral override

> **Rule**: Encrypted-in-DB is the default. Ephemeral per-request override for one-off keys.

Resolution order: agent_secret_overrides → user_secrets → process .env
