# Elements Reference

## Environment Variables

### Required

```bash
TWELVE_DATA_API_KEY=...        # OHLCV candles, historical data
# LLM (at least one)
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
DEEPSEEK_API_KEY=...
GEMINI_API_KEY=...
```

### Optional

```bash
CMC_API_KEY=...                # Token metadata only (logo, description, supply)
MONGODB_URI=mongodb+srv://...  # Cache layer
TRACKED_SYMBOLS=BTC,ETH,BNB,SOL  # Symbols for background cache refresh
LLM_PROVIDER=gemini            # Force provider (openai|anthropic|deepseek|gemini)
LLM_MODEL=gemini-2.5-flash    # Force model
```

Pyth Hermes requires no API key (public endpoint).

### Rate Limits

- **Twelve Data free**: 8 calls/min
- **CMC free**: 333 calls/day, 30 calls/min
- **Pyth Hermes**: No strict limit (public)

## Pyth Price Feeds

27 symbols supported via `app/pyth_client.py`. Feed IDs verified against `hermes.pyth.network`.

```
BTC  ETH  BNB  SOL  XRP  ADA  DOGE  AVAX  DOT  LINK
UNI  ATOM LTC  NEAR APT  ARB  OP    SUI   INJ  AAVE
FIL  PEPE POL  BCH  ETC  XLM  HBAR
```

HSK has no Pyth feed.

Symbol normalization: `BTCUSDT` / `BINANCE:ETHUSDT` / `BTC/USD` / `BTC` all resolve to the same feed.

## Trading Algorithms (30+)

### Momentum (8)

| Algo | Params | Signal |
|------|--------|--------|
| `momentum` | lookback=20 | Return over lookback |
| `dual_momentum` | short=10, long=50 | Short vs long momentum |
| `breakout` | lookback=20 | N-period high/low break |
| `donchian_channel` | lookback=20 | Donchian breakout |
| `ma_crossover` | fast=10, slow=50 | SMA cross |
| `ema_crossover` | fast=12, slow=26 | EMA cross |
| `macd_signal` | fast=12, slow=26, signal=9 | MACD vs signal line |
| `adx_filter` | period=14, threshold=25 | ADX trending filter |

### Mean Reversion (6)

| Algo | Params | Signal |
|------|--------|--------|
| `z_score` | lookback=20, threshold=2.0 | Z-score inversion |
| `bollinger_reversion` | lookback=20, num_std=2.0 | Band reversion |
| `rsi_signal` | period=14, oversold=30, overbought=70 | RSI extremes |
| `stochastic_signal` | k=14, d=3 | %K/%D cross |
| `range_sr` | lookback=20 | Support/resistance fade |
| `mean_reversion` | (alias for z_score) | |

### Trend (4)

| Algo | Params |
|------|--------|
| `supertrend` | atr_period=10, multiplier=3.0 |
| `ichimoku_signal` | tenkan=9, kijun=26 |
| `trend_following` | (alias for ma_crossover) |
| `adx_filter` | (dual category) |

### Volatility (3)

| Algo | Params |
|------|--------|
| `atr_breakout` | atr_period=14, threshold=1.5 |
| `bollinger_squeeze` | lookback=20, num_std=2.0, squeeze=0.5 |
| `keltner_bollinger` | lookback=20, atr_mult=2.0, bb_std=2.0 |

### Volume (3)

| Algo | Params |
|------|--------|
| `vwap_deviation` | lookback=20, threshold=0.01 |
| `obv_trend` | lookback=20 |
| `funding_bias_stub` | (returns 0 — no data source) |

### Statistical (2)

| Algo | Params |
|------|--------|
| `linear_regression_channel` | lookback=50, num_std=2.0 |
| `kalman_fair_value` | process_var=0.01, measurement_var=1.0 |

All return `(signal: float, detail: str)`. signal > 0 = bullish, < 0 = bearish, 0 = neutral.

## Market Features (MarketAnalyzer)

Computed from candles, passed to LLM for strategy selection.

| Category | Features |
|----------|----------|
| Volatility | ATR, realized_vol (recent + medium), vol_ratio |
| Trend | ADX, MA slope, range compression/expansion flags |
| Liquidity | Spread proxy, wickiness, churn metric |
| Funding/OI | Stubs (no data source) |

Output: `MarketRegimeSummary` — all features in one Pydantic model.

## Pydantic Schemas

### StartRequest

```python
{
  "symbol": "BTCUSDT",
  "amount_usdt": 1000,
  "leverage": 5,
  "risk_profile": "moderate",       # conservative|moderate|aggressive
  "primary_timeframe": "15m",
  "poll_seconds": 1.0,
  "tp_pct": 0.03,
  "sl_pct": 0.02,
  "tp_sl_mode": "fixed",            # fixed|dynamic
  "live_mode": false,
  "supervisor_interval_seconds": 60,
  "llm_provider": "gemini",
  "indicators": ["rsi", "macd"]     # optional user-selected
}
```

### StatusResponse

```python
{
  "running": true,
  "symbol": "BTCUSDT",
  "last_price": 72160.15,
  "side": "LONG",                    # FLAT|LONG|SHORT
  "entry_price": 71800.0,
  "position_size_usdt": 1000.0,
  "leverage": 5,
  "unrealized_pnl_usdt": 25.0,
  "last_action": "OPEN_LONG",
  "last_reason": "EMA crossover bullish",
  "active_strategy": "ema_crossover"
}
```

### StrategyPlan

```python
{
  "strategy": "ema_crossover",
  "lookback": 20,
  "threshold": 0.5,
  "max_loss_pct": 0.02,
  "direction": "long"
}
```

### Candle

```python
{
  "timestamp": datetime,
  "open": float,
  "high": float,
  "low": float,
  "close": float,
  "volume": float
}
```

### Log Entry

```python
{
  "ts": "2026-04-10T12:07:13.688Z",
  "level": "init|llm|start|tick|action|sl_tp|stop|error|warn|supervisor",
  "message": "[INIT] Starting trading session for BTCUSDT"
}
```

## agents.json Schema

```json
[
  {
    "agent_id": "btcusdt-8010",
    "symbol": "BTCUSDT",
    "amount_usdt": 1000.0,
    "leverage": 5,
    "risk_profile": "moderate",
    "port": 8010,
    "pid": null,
    "created_at": "2026-04-10 14:30",
    "alive": false,
    "name": "BTC Agent",
    "timeframe": "15m",
    "poll_seconds": 1.0,
    "tp_pct": 0.03,
    "sl_pct": 0.02,
    "tp_sl_mode": "fixed",
    "live_mode": false,
    "supervisor_interval": 60.0,
    "llm_provider": "gemini"
  }
]
```

API keys (`exchange_api_key`, `exchange_secret`, `llm_api_key`) are excluded from persistence — memory-only.

## LLM Providers

| Provider | Models | Env Var |
|----------|--------|---------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo | `OPENAI_API_KEY` |
| Anthropic | claude-sonnet-4-5, claude-3-5-sonnet, claude-3-5-haiku | `ANTHROPIC_API_KEY` |
| DeepSeek | deepseek-chat, deepseek-reasoner, deepseek-r1 | `DEEPSEEK_API_KEY` |
| Gemini | gemini-2.0-flash, gemini-2.5-pro, gemini-2.5-flash | `GEMINI_API_KEY` |

Auto-detection: uses first available key. Override with `LLM_PROVIDER` env var or per-agent config in TUI.

## Dependencies

```
fastapi==0.115.6       uvicorn[standard]==0.30.6   httpx==0.27.2
pydantic==2.9.2        openai>=1.10.0              anthropic>=0.39.0
requests>=2.28.0       python-dotenv>=1.0.0        pymongo>=4.6.0
apscheduler>=3.10.0    textual>=0.52.0
```
