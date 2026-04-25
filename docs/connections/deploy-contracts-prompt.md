# Contract Deployment Prompt — Initia MiniEVM

Paste this prompt into Claude Code (or any code-aware agent) from the repo root.
It handles everything end-to-end: write contracts → compile → deploy → save addresses.

---

```
I need to deploy two Solidity audit-log contracts to the Initia MiniEVM testnet for the Artic trading platform.

## Context

- Chain: Initia MiniEVM testnet
- RPC: https://jsonrpc-evm-1.anvil.asia-southeast.initia.xyz
- Chain ID: 2594729740794688
- Toolchain: Foundry (forge). Use --legacy flag on all deployments (required for Initia).
- Output: write deployed addresses + ABIs to contracts/deployed.json and contracts/trade_logger_deployed.json

## Step 1 — Verify Foundry is installed

Run: forge --version
If missing, install: curl -L https://foundry.paradigm.xyz | bash && foundryup

## Step 2 — Write DecisionLogger.sol

Create contracts/src/DecisionLogger.sol with this interface:

Event: DecisionLogged(bytes32 indexed sessionId, bytes32 indexed symbol, uint8 action, uint8 strategy, uint8 confidence, int16 pnlBps, bytes32 reasoningHash, uint256 timestamp)

Function: logDecision(bytes32 sessionId, bytes32 symbol, uint8 action, uint8 strategy, uint8 confidence, int16 pnlBps, bytes32 reasoningHash) external

Action codes: 0=HOLD 1=OPEN_LONG 2=OPEN_SHORT 3=CLOSE 4=ADJUST
Strategy codes: 0=simple_momentum ... 255=llm_auto (see app/onchain_logger.py STRATEGY_INDEX)

## Step 3 — Write TradeLogger.sol

Create contracts/src/TradeLogger.sol with this interface:

Event: TradeLogged(bytes32 indexed sessionId, bytes32 indexed symbol, uint8 side, uint256 entryPrice, uint256 exitPrice, int16 pnlBps, bytes32 detailHash, uint256 timestamp)

Function: logTrade(bytes32 sessionId, bytes32 symbol, uint8 side, uint256 entryPrice, uint256 exitPrice, int16 pnlBps, bytes32 detailHash) external

Side codes: 0=OPEN_LONG 1=OPEN_SHORT 2=CLOSE_LONG 3=CLOSE_SHORT
Prices are scaled by 1e8.

## Step 4 — Initialize Foundry project

Run from repo root:
cd contracts && forge init --no-git --force (if contracts/ doesn't already have foundry.toml)
Or if contracts/ doesn't exist: forge init contracts --no-git

## Step 5 — Compile

cd contracts && forge build

Fix any compilation errors before proceeding.

## Step 6 — Deploy both contracts

Use the CHAIN_PRIVATE_KEY environment variable for the deployer key.
The key must be a hex private key (0x-prefixed) of a wallet funded on Initia MiniEVM testnet.
Get testnet funds at: https://app.testnet.initia.xyz/faucet (use the EVM address of the key).

Deploy DecisionLogger:
forge create src/DecisionLogger.sol:DecisionLogger \
  --rpc-url https://jsonrpc-evm-1.anvil.asia-southeast.initia.xyz \
  --private-key $CHAIN_PRIVATE_KEY \
  --legacy

Deploy TradeLogger:
forge create src/TradeLogger.sol:TradeLogger \
  --rpc-url https://jsonrpc-evm-1.anvil.asia-southeast.initia.xyz \
  --private-key $CHAIN_PRIVATE_KEY \
  --legacy

## Step 7 — Save artifacts

After each deploy, extract the deployed address from forge output and:

1. Write contracts/deployed.json:
{
  "address": "<DecisionLogger deployed address>",
  "abi": [ <full ABI array from contracts/out/DecisionLogger.sol/DecisionLogger.json> ]
}

2. Write contracts/trade_logger_deployed.json:
{
  "address": "<TradeLogger deployed address>",
  "abi": [ <full ABI array from contracts/out/TradeLogger.sol/TradeLogger.json> ]
}

## Step 8 — Update .env.dev

Add these lines to .env.dev:
CHAIN_RPC_URL=https://jsonrpc-evm-1.anvil.asia-southeast.initia.xyz
CHAIN_PRIVATE_KEY=<the funded wallet private key>

## Step 9 — Verify

Call a read on each contract to confirm deployment:
cast call <DecisionLogger address> "owner()(address)" --rpc-url https://jsonrpc-evm-1.anvil.asia-southeast.initia.xyz
(If no owner function, just verify the bytecode is non-empty.)

## Step 10 — Report

Tell me:
- DecisionLogger address
- TradeLogger address  
- Deployer EVM address
- Any errors encountered
```
