# Alpha Architecture

One-page view. Details live in sibling docs.

## Diagram

```
                  ┌───────────────────────┐
                  │  CLIENT (web, bun)    │
                  └──────────┬────────────┘
                             │ HTTPS + WSS
                             ▼
                  ┌──────────────────────────────────────────────┐
                  │                 CENTRAL HUB                   │
                  │                                               │
                  │  auth · router · wake · credits · marketplace │
                  │  market cache · indexer mirror · OTel · funder│
                  │                                               │
                  │  Postgres(users, credits, ledger, mkt, idx..) │
                  └──────────────────┬───────────────────────────┘
                                     │ wake/drain/proxy (mTLS)
                                     ▼
                  ┌──────────────────────────────────────────────┐
                  │         USER VM  (Firecracker/Fly)            │
                  │         lifecycle: scale-to-zero              │
                  │  ┌──────────────────────────────────────────┐ │
                  │  │   USER-SERVER                            │ │
                  │  │   agent orchestration · LLM proxy        │ │
                  │  │   chain signer · local indexer           │ │
                  │  │   strategy store · RestrictedPython      │ │
                  │  │   Postgres(agents, trades, logs, idx…)   │ │
                  │  └──────┬─────────┬─────────┬───────────────┘ │
                  │         ▼         ▼         ▼                  │
                  │     [Agent]   [Agent]   [Agent]                │
                  │     one symbol each — tick loop                │
                  └──────┬───────────┬───────────┬──────────────┘
                         │           │           │
           Pyth Hermes   │           │           │   HashKey Chain
        (live prices, no key)        │    (testnet; DecisionLogger, TradeLogger)
                                     ▼
                            LLM provider (OpenAI/Anthropic/…)
```

## Component responsibilities

| Component | Owns | Does not touch |
|-----------|------|---------------|
| Client | UI state, auth token storage | chain keys, LLM keys |
| Hub | auth, routing, cross-user data, billing, market cache, indexer mirror, OTel | user strategy code execution, LLM calls, chain signing |
| User-Server | this user's agents, strategies, LLM proxy, chain signer, local indexer | other users' data, market data fetching, credit state |
| Agent | one symbol's tick loop, signal compute, local position | DB, LLM, chain, other agents |
| Strategy | `(plan, prices, candles) → (signal, detail)` | network, filesystem, process |

## Data flow directions

| Path | Direction | Purpose |
|------|-----------|---------|
| client → hub | HTTPS | all API + WebSocket |
| hub → user-server | HTTPS proxy | routed client requests, credit-halt, drain, flush |
| user-server → hub | HTTPS | indexer sync, credit heartbeat, OTel |
| user-server → agent | HTTP (internal network) | spawn, /start, /stop, status polls |
| agent → user-server | HTTP (internal network) | push status, trades, logs, supervisor events |
| user-server → LLM | HTTPS | strategy pick + supervisor |
| user-server → chain | RPC | trade + supervisor txs |
| hub → market providers | HTTPS | candle + price cache fill |
| agent → Pyth | HTTPS | live price (free, no key) |

## Key invariants

- Clients only talk to hub (hub proxies everything user-scoped)
- Agent never reaches hub or external providers except Pyth — all other network through user-server
- User API keys live in hub (encrypted) and user-server (decrypted in memory only on wake); never in agent env
- User strategy code never runs outside RestrictedPython
- Credits debit happens on hub only — user-server cannot self-report
- Chain tx signing happens only on user-server (one wallet per user VM)
- Market cache is hub-owned — user-server reads through, never calls market providers directly

## See also

- Runtime lifecycle flows: [runtime-flow.md](runtime-flow.md)
- Who owns what data: [system-map.md](system-map.md)
- API specs: [api-contracts.md](api-contracts.md)
- DB schemas: [data-model.md](data-model.md)
- Trust & secrets: [security-model.md](security-model.md)
