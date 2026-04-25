# On-Chain Audit Log — Initia MiniEVM

Artic logs every AI trading decision and trade event to an immutable on-chain audit trail.
This is a logging-only integration: the chain does not custody funds or execute trades.

## Why Initia MiniEVM

Artic is an AI/Tooling platform. The on-chain component provides verifiable, tamper-proof
records of what the AI decided and why — useful for accountability, auditing, and showcasing
AI decision transparency. MiniEVM (Solidity + web3.py) was chosen for minimal integration
surface: existing `OnchainLogger` and `OnchainTradeLogger` work with only a provider URL swap.

## Contracts

| Contract | Purpose | File |
|---|---|---|
| `DecisionLogger` | Logs supervisor AI decisions (KEEP/CLOSE/ADJUST) | `contracts/DecisionLogger.sol` |
| `TradeLogger` | Logs trade open/close events with PnL | `contracts/TradeLogger.sol` |

Both deployed to: **Initia MiniEVM testnet**
RPC: `https://jsonrpc-evm-1.anvil.asia-southeast.initia.xyz`
Chain ID: `2594729740794688`

Deployed addresses stored in:
- `contracts/deployed.json` → DecisionLogger address + ABI
- `contracts/trade_logger_deployed.json` → TradeLogger address + ABI

## Signing Key

A single **platform key** (`CHAIN_PRIVATE_KEY`) signs all on-chain log txs across all agents.
This key is injected into agent containers by the user-server spawner at container start.
The platform wallet should be funded on the MiniEVM testnet via the Initia faucet.

## What Gets Logged

### DecisionLogger — supervisor decisions (every ~60s while in position)

| Field | Type | Value |
|---|---|---|
| `session_id` | bytes32 | keccak(agent_id + symbol + timestamp) |
| `symbol` | bytes32 | keccak(trading symbol) |
| `action` | uint8 | 0=HOLD 1=OPEN_LONG 2=OPEN_SHORT 3=CLOSE 4=ADJUST |
| `strategy` | uint8 | strategy index (see `STRATEGY_INDEX` in `onchain_logger.py`) |
| `confidence` | uint8 | 0–100 |
| `pnl_bps` | int16 | unrealized PnL in basis points |
| `reasoning_hash` | bytes32 | keccak(LLM reasoning text) |

### TradeLogger — trade open/close events

| Field | Type | Value |
|---|---|---|
| `session_id` | bytes32 | keccak(agent_id + symbol + timestamp) |
| `symbol` | bytes32 | keccak(trading symbol) |
| `side` | uint8 | 0=OPEN_LONG 1=OPEN_SHORT 2=CLOSE_LONG 3=CLOSE_SHORT |
| `entry_price` | uint256 | price × 1e8 |
| `exit_price` | uint256 | price × 1e8 (0 for open events) |
| `pnl_bps` | int16 | realized PnL in basis points (0 for open events) |
| `detail_hash` | bytes32 | keccak(JSON: size_usdt, leverage, strategy, reason) |

## Env Vars Required (agent container)

| Var | Description |
|---|---|
| `CHAIN_RPC_URL` | Initia MiniEVM JSON-RPC endpoint |
| `CHAIN_PRIVATE_KEY` | Platform wallet private key (hex, 0x-prefixed) |

Both injected by `user-server/user_server/agents/spawner.py` from hub secrets.
On-chain logging is **gracefully disabled** if either var is absent — no crash.

## Data Flow

```
Agent container
  └─ engine.py tick / supervisor check
       ├─ OnchainLogger.log_decision()   → DecisionLogger contract (supervisor decisions)
       ├─ OnchainTradeLogger.log_trade() → TradeLogger contract (trade open/close)
       └─ hub_callback.report_onchain_*  → user-server /onchain-decisions, /onchain-trades
                                              └─ stored in DB for dashboard display
```

## Adding On-Chain Fields

1. Add field to Solidity event in `contracts/DecisionLogger.sol` or `contracts/TradeLogger.sol`
2. Redeploy with Foundry (`--legacy` flag required for Initia)
3. Update ABI in `contracts/deployed.json` / `contracts/trade_logger_deployed.json`
4. Update encoder in `app/onchain_logger.py` or `app/onchain_trade_logger.py`
5. Update this doc
