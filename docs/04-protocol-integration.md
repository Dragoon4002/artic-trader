# Protocol Integration

## Current State

### Pyth Network — PRIMARY PRICE SOURCE

**Status:** Active. All live prices come from Pyth.

**Module:** `app/pyth_client.py`

**Endpoint:** `GET https://hermes.pyth.network/v2/updates/price/latest?ids[]=<feed_id>`

**Coverage:** 27 crypto symbols (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, LINK, UNI, ATOM, LTC, NEAR, APT, ARB, OP, SUI, INJ, AAVE, FIL, PEPE, POL, BCH, ETC, XLM, HBAR)

**How it works:**
- Feed IDs hardcoded per symbol (verified against Hermes API)
- `PythClient.get_price(symbol)` → single REST call → parse `int(price) * 10^expo`
- `PythClient.get_prices_batch(symbols)` → multi-id call → dict of prices
- Retry logic: 3 attempts, 0.3s backoff
- No API key needed

**What Pyth provides:** Real-time price + confidence interval + publish timestamp

**What Pyth does NOT provide:** Volume, market cap, % change, token metadata, historical candles

### Twelve Data — CANDLES & HISTORICAL

**Status:** Active. All OHLCV data comes from Twelve Data.

**Module:** `app/market.py`

**Used for:** Strategy computation, chart endpoints, historical analysis

**Rate limit:** 8 calls/min on free tier (candle refresh spaced 8s apart in background)

### CoinMarketCap — METADATA ONLY

**Status:** Optional. Used only for token detail pages.

**Module:** `app/cmc_client.py`

**Provides:** Token description, logo URL, website/social URLs, contract address, supply data, tags

**NOT used for:** Live prices (replaced by Pyth)

Price field in CMC responses is overridden with Pyth price before returning to clients.

### Blockchain Execution — STUB

**Status:** Not implemented.

**Module:** `app/pancake_executor_stub.py`

All methods log warnings and return mock responses. The system is paper-trading only.

## What Would Need to Change for Live Trading

### 1. Executor Interface

Replace the stub with a real executor. Suggested interface:

```python
class BaseExecutor(ABC):
    async def place_order(self, symbol, side, size_usdt, price) -> dict
    async def get_positions(self, symbol) -> list
    async def close_position(self, symbol) -> dict
```

### 2. Candidate Protocols

| Protocol | Type | Chain | Leverage | Complexity |
|----------|------|-------|----------|------------|
| Pancake Perps | AMM Perps | BNB Chain | Up to 150x | Medium (Web3) |
| GMX | GLP Perps | Arbitrum/Avax | Up to 50x | Medium (Web3) |
| dYdX | Order Book | StarkEx | Up to 20x | Easy (REST) |
| Hyperliquid | Native L1 | Hyperliquid | Up to 50x | Easy (REST) |
| HashKey | CEX | HashKey Chain | TBD | TBD |

### 3. Requirements for Live

- Web3 library (for on-chain protocols)
- Private key management (encrypted storage)
- Gas fee estimation + BNB/ETH balance checks
- Transaction retry logic
- On-chain position reconciliation
- Audit trail (tx hashes, block numbers)

### 4. Engine Changes

`engine.py` currently calls `PaperPosition` methods. For live:

```python
if self._live_mode:
    result = await self._trading_client.place_order(...)
else:
    self.position.open_long(...)
```

The plumbing exists (`_live_mode` flag, `_trading_client` field) — just needs a real executor implementation.
