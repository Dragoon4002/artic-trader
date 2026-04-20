# Plan — User VM (User-Server + Agents)

One VM per user. Contains: user-server (orchestrator), N agent containers (trading engines), local Postgres (agents, trades, logs, strategies, indexer). Scale-to-zero controlled by hub.

## VM image

- Base: Ubuntu 22.04 minimal or Firecracker-optimized rootfs
- Installed: Python 3.12, Docker (for agent containers), Postgres 16
- Services: `user-server.service` (systemd), `postgres.service`, `docker.service`
- Boot target: systemd multi-user with user-server auto-start
- Shipped via image registry; hub records `image_tag` per VM

## Boot sequence (wake)

```
1. VM resume (Firecracker/Fly)
2. systemd brings up postgres → docker → user-server
3. user-server loads:
     - local Postgres migrations (Alembic auto-upgrade)
     - chain wallet private key (decrypt from VM keystore with boot-time KEK from hub)
     - self mTLS cert from disk
4. user-server exposes :8443 (hub mTLS), :8444 (health)
5. hub polls /health, then POST /hub/secrets/refresh → user-server caches decrypted LLM/CEX keys in memory
6. VM ready for traffic
```

## Directory layout (new top-level `user-server/`)

```
user-server/
├── main.py                 # FastAPI app
├── config.py               # env + VM-local paths
├── db/
│   ├── base.py
│   ├── migrations/
│   └── models/             # agents, trades, log_entries, strategies, indexer_tx
│
├── agents/
│   ├── router.py           # /agents/* (called by hub proxy)
│   ├── service.py          # create, start, stop, delete, list
│   ├── spawner.py          # docker-sdk wrapper for agent containers
│   └── registry.py         # in-process live state (port, container_id, alive)
│
├── strategies/
│   ├── router.py           # /strategies/* CRUD
│   ├── service.py          # install, remove
│   ├── runner.py           # RestrictedPython executor
│   └── builtins/           # symlink or copy of /app/strategies/quant_algos
│
├── llm/
│   ├── router.py           # /llm/plan, /llm/supervise, /llm/chat
│   ├── providers.py        # dispatch to openai / anthropic / deepseek / gemini
│   └── rate_limit.py       # per-user quota
│
├── chain/
│   ├── signer.py           # sign + send TradeLogger / DecisionLogger txs
│   ├── wallet.py           # keystore management
│   └── retry.py            # gas bump on stuck
│
├── indexer/
│   ├── writer.py           # INSERT on tx success
│   ├── query.py            # /hub/indexer/since
│   └── flusher.py          # pre-drain push to hub
│
├── hub_callback/
│   ├── secrets.py          # accepts /hub/secrets/refresh
│   ├── drain.py            # /hub/drain handler
│   └── halt.py             # /hub/halt handler
│
├── otel.py                 # span/log export to hub
└── systemd/
    └── user-server.service
```

## Endpoints served

Consumed by hub (mTLS + X-Hub-Secret):

- `/health`
- `/agents/*` (CRUD, start, stop, status, logs, trades, start-all, stop-all)
- `/strategies/*`
- `/llm/*`
- `/hub/drain`, `/hub/halt`, `/hub/secrets/refresh`, `/hub/indexer/since`

Consumed by local agents (INTERNAL_SECRET):

- `/agents/{id}/status` (push)
- `/trades` (push)
- `/logs` (push)
- `/supervisor` (push)
- `/llm/plan`, `/llm/supervise`, `/llm/chat` (LLM proxy for agents)

## Agent container

Image: `artic-app:latest` (existing, refactored per below).

### Refactors required

| File | Change |
|------|--------|
| `app/engine.py` | replace direct OpenAI/Anthropic calls with HTTP POST to user-server `/llm/*` |
| `app/config.py` | remove `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, … ; add `USER_SERVER_URL` |
| `app/hub_callback.py` | rename → `app/us_callback.py`; target is user-server, not hub |
| `app/onchain_logger.py`, `app/onchain_trade_logger.py` | remove — user-server now owns chain signing |
| `app/llm/llm_planner.py` | becomes a client for user-server LLM proxy |
| `app/strategies/` | stay in image as built-ins; user strategies loaded dynamically from user-server |

### Agent env (injected by user-server at spawn)

```
HUB_AGENT_ID=<uuid>
SYMBOL=BTCUSDT
USER_SERVER_URL=http://user-server:8443
INTERNAL_SECRET=<per-spawn>
STRATEGY_POOL=["ema_crossover", "z_score", "marketplace:<uuid>"]
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
RISK_PARAMS={"amount_usdt":100,"leverage":5,...}
```

No API keys in env. No hub URL in env. No chain URL in env.

### Agent endpoints unchanged

- `GET /health`, `POST /start`, `POST /stop`, `GET /status`, `GET /logs`

## Strategy runner (RestrictedPython)

```python
# simplified
def run_strategy(strat: Strategy, plan, price_history, candles):
    if strat.source == "builtin":
        return builtins[strat.name](plan, price_history, candles)

    # authored or marketplace
    compiled = compile_restricted(strat.code_blob, "<strategy>", "exec")
    globs = {
        "__builtins__": safe_builtins | {"math": math, "statistics": statistics},
        "_getattr_": guarded_getattr,
        "_getitem_": default_guarded_getitem,
        "_getiter_": default_guarded_getiter,
    }
    locs = {}
    with timeout(ms=500), memory_guard(mb=64):
        exec(compiled, globs, locs)
        return locs["compute"](plan, price_history, candles)
```

Violations (bad import, timeout, memory) → log `error`, fall back to `simple_momentum`.

## LLM proxy behavior

- Keys cached in memory post-wake (`/hub/secrets/refresh` pushes them)
- Per-user rate limit: 60 calls/min; per-agent budget tracker for observability
- Provider SDKs: `openai`, `anthropic`, `google-generativeai`, `deepseek` (lazy-imported)
- Per-request model selection honours agent's config
- Response logged with OTel span (provider, model, tokens, latency)

## Chain signer

- Uses user VM's testnet wallet (EOA)
- Pulls ABI from `contracts/deployed.json` (bundled in image)
- Retries with gas bump: 3 attempts, +20% gas each
- On success: INSERT `indexer_tx`; UPDATE target `trades.tx_hash` or emit supervisor record
- On final failure: log WARN, metric counter; trade not retried (accept single-tx semantics)

## Local indexer

- Appended on chain-tx success
- Identical schema to hub mirror
- Flush: batch push to hub on 30min cron (pulled by hub) + forced pre-drain

## Scale-to-zero behavior

When hub calls `POST /hub/drain`:
1. Refuse new `/agents/*/start`
2. Call `/agents/stop-all` (idempotent — user-server stops all active agents, waits ≤30s for tick loops to exit)
3. Flush indexer batch to hub
4. fsync Postgres WAL
5. Return 200 to hub

Hub then snapshots + stops VM.

## Failure modes

| Failure | Handling |
|---------|----------|
| Agent container crash | Docker `restart=on-failure:3`; user-server detects via status 502 → re-POSTs `/start` |
| Strategy sandbox violation | logged, fall back to `simple_momentum`, continue tick |
| LLM provider error / 429 | per-request retry ≤2, then use last successful plan; supervisor returns KEEP |
| Chain RPC down | retry ≤3 with gas bump; if all fail, log WARN and skip — indexer row not written |
| Local Postgres down | user-server refuses writes; hub proxy returns 503; hub marks VM `error`; admin manual |
| VM cold-wake takes >10s | hub returns 202 `VM_WAKING`, client retries; repeat wake failures → mark VM `error` |

## Observability

- OTel spans: wake, agent lifecycle events, tick timings, LLM calls, chain calls, sandbox violations
- Metrics: `tick_duration_ms`, `llm_latency_ms{provider}`, `chain_tx_confirm_ms`, `sandbox_violation_total`, `strategy_error_total{name}`
- Logs: structured JSON to stdout → hub OTel collector

## Out of scope (alpha)

- Live HashKey executor (paper only)
- HSM/MPC wallet
- Hot-reloading strategy code mid-session (restart required)
- Cross-agent shared state (each agent is isolated)
- Agent→agent communication
