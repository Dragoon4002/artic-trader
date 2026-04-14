# Env & Secrets — Artic

## Secret Resolution Order

1. **Ephemeral override** — per-request API key in start request body (highest priority, never stored)
2. **agent_secret_overrides** — per-agent encrypted values in DB
3. **user_secrets** — user-level encrypted defaults in DB
4. **Process .env** — hub host environment fallback

First match wins. If no match, agent operates without that key.

## Known Secret Key Names

| Key | Used By | Purpose |
|-----|---------|---------|
| TWELVE_DATA_API_KEY | hub/market_cache | Candle data (hub-managed) |
| OPENAI_API_KEY | app/llm/llm_planner.py | OpenAI LLM provider |
| ANTHROPIC_API_KEY | app/llm/llm_planner.py | Anthropic LLM provider |
| DEEPSEEK_API_KEY | app/llm/llm_planner.py | DeepSeek LLM provider |
| GEMINI_API_KEY | app/llm/llm_planner.py | Google Gemini LLM provider |
| CMC_API_KEY | app/market/cmc_client.py | CoinMarketCap metadata |
| LLM_PROVIDER | app/llm/llm_planner.py | Which LLM provider |
| LLM_MODEL | app/llm/llm_planner.py | Which model |
| HASHKEY_API_KEY | app/executor/hashkey.py | HashKey Global exchange |
| HASHKEY_SECRET | app/executor/hashkey.py | HashKey Global signing |
| HASHKEY_SANDBOX | app/executor/hashkey.py | true=sandbox, false=production |
| HSK_RPC_URL | app/onchain_logger.py | HashKey Chain RPC endpoint |
| HSK_PRIVATE_KEY | app/onchain_logger.py | Contract deployer/caller key |
| INTERNAL_SECRET | hub + app | Agent→hub push auth |

## Rules

- **API keys never persisted in plaintext** — not in DB, not in logs, not in config files
- Agents receive secrets as **Docker env vars at spawn**
- Encrypted-in-DB uses AES — see `/docs/connections/auth-flow.md`
- Never log secret values — mask in all output
- When adding a new key: add to this table, update relevant module docs
