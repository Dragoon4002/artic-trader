# Artic Alpha — Project Details

End-to-end reference for the alpha cut. Read this first; every other doc in `docs/alpha/` refines a slice of what's here.

## What Artic is

Multi-tenant SaaS for AI-driven crypto futures trading. Each user owns N isolated trading agents. A user-supplied LLM picks a quant strategy per agent and acts as a supervisor. Paper trades by default; live trading via HashKey Global (implementation lands post-alpha). On-chain logging of trades and supervisor decisions on HashKey Chain.

## Alpha scope

- **User cap**: 100 concurrent users
- **Chain**: testnet only; platform-funded user-server wallets
- **Live exchange**: disabled (HashKey executor unfinished)
- **Billing**: credit system, `1 AH = 1 agent-hour`, debited per-minute
- **Strategy marketplace**: public, free-for-all, report/delist moderation
- **Isolation**: VM-per-user (scale-to-zero)
- **Sandbox**: RestrictedPython for user-supplied strategies

## Components (top level)

| Component | Role | Runs where |
|-----------|------|-----------|
| Client (web dashboard) | UI for auth, agent control, marketplace | browser |
| Central Hub | Auth, routing, wake, credits, market cache, marketplace, indexer mirror, observability | single persistent server |
| User VM | Per-user compute — contains user-server + agents | Firecracker/Fly Machines, scale-to-zero |
| User-Server | Orchestrates this user's agents, LLM proxy, chain signer, local indexer, strategy store | inside user VM |
| Agent | One process per trading symbol — tick loop, signal compute, executor | inside user VM |
| HashKey Chain | On-chain trade + supervisor logging via DecisionLogger + TradeLogger contracts | external |
| Market providers | Pyth Hermes (prices), TwelveData (candles), CMC (metadata) | external |
| LLM providers | OpenAI, Anthropic, DeepSeek, Gemini | external |

## User journey

1. **Connect wallet** → InterwovenKit popup → user signs nonce + session-key auth message → hub verifies signature → UPSERT user by `(wallet_address, wallet_chain)` → issues JWT + session_id; if first-time: VM provisioned (stopped). Resolves `.init` username in-line, caches on user row.
2. **First dashboard load** → hub cold-wakes user VM; client sees "warming up" ≤10s
3. **Add LLM key** → user pastes API key into dashboard → encrypted → stored in hub secrets → injected at user-server wake
4. **Create agent** → dashboard → hub → user-server → spawn agent container with `SYMBOL`, `LLM_PROVIDER`, `LLM_MODEL`, strategy pool. State-changing requests carry session-key headers (auto-signed by dashboard; no wallet popup).
5. **Start agent** → user-server POSTs `/start` to agent → agent runs tick loop
6. **Trade** → agent signals → user-server executes (paper) → user-server signs tx with platform-custodied VM wallet → HashKey Chain → tx hash → local indexer + mirrored to hub on next sync
7. **Dashboard live view** → WebSocket from hub (proxied from user-server) → real-time status/logs/PnL
8. **Scale-to-zero** → `agents_alive==0 AND dashboard_idle>5min` → hub drains user-server → snapshots VM
9. **Credits depleted** → hub halts all user's agents, notifies via dashboard

## Lifecycle summary

```
CONNECT ─► wallet sign (nonce + session key) ─► UPSERT user ─► [on first: VM provisioned, stopped]
REQUEST ─► hub wake-proxy ─► VM starts ─► user-server healthy ─► serve request
CREATE AGENT ─► user-server spawns agent container (scoped to user VM)
START   ─► agent tick loop begins; status pushed to user-server every tick
IDLE    ─► alive==0 AND no dashboard traffic 5m ─► VM snapshot + stop
WAKE    ─► next client request triggers VM resume (≤10s)
```

## Initia integrations (alpha)

Two features shipped to integrate with the Initia UX stack. Required to use `@initia/interwovenkit-react` for all wallet UI.

| Feature | What it does | Where it shows up |
|---------|-------------|-------------------|
| `.init` usernames | Reverse-lookup `wallet_address → alice.init` at `/auth/verify`; cached 24h on `users.init_username` | Header, leaderboard, marketplace publisher, agent detail owner field |
| Auto-signing session keys | One wallet popup at connect authorizes an ephemeral session key. Dashboard signs state-changing requests with it, no wallet popup per action | All POST/PATCH/DELETE endpoints touching user state |

Interwoven Bridge is deferred to beta (alpha is paper trading; no cross-rollup asset movement).

## Billing (alpha)

- Ledger: `credits(user_id, balance)` + append-only `credit_ledger`
- Meter: hub cron every minute debits `1/60 AH` per alive agent
- Halt: on `balance <= 0` hub pushes stop-all to user-server
- Topup: admin grant only; Stripe/on-chain payments = beta

## On-chain

- Alpha = testnet. Platform funds each user-server's chain wallet every 5h to configurable floor
- Each trade and each supervisor decision → tx from user-server
- Tx hash stored in **local user-server indexer** + **hub mirror** (sync every 30min + pre-drain flush)
- Contracts unchanged: `DecisionLogger.sol`, `TradeLogger.sol`

## Strategy marketplace

- Any user can publish a strategy — Python code running under RestrictedPython
- Install = copy code into installer's user-server DB (no live link — delist doesn't break existing installs)
- Moderation: report/delist. `reports >= 3 in 7 days` → auto-hide + manual review
- Strategies receive `(plan, price_history, candles) → (signal: float, detail: str)` and nothing else

## What's out of scope for alpha

- HashKey live executor (remains skeleton)
- Mainnet chain
- Stripe / on-chain payment billing
- Custom VM spec upgrades (t-shirt sizes)
- Warm pool for new-signup latency
- TUI / CLI / Telegram clients (all alpha interaction is via web dashboard)
- Migration tooling for user-server image rollouts

## Beta graduation criteria

- Live HashKey executor + production exchange keys
- Mainnet on-chain logging with user wallets
- Stripe / on-chain credit topups
- Subprocess-level strategy sandbox (seccomp + cgroups)
- User-server rolling-upgrade operator
- 1000+ concurrent users
- SLA + on-call
