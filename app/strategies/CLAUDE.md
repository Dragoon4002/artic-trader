# Strategies Module — Artic

All quant trading algorithms and the signal dispatcher. LLM selects a strategy by name; `signals.py` routes to the correct algo.

## Folder Structure

```
strategies/
├── signals.py                    # Dispatcher: strategy name → algo
└── quant_algos/
    ├── momentum_algos.py         # 8 momentum algorithms
    ├── mean_reversion_algos.py   # 6 mean reversion algorithms
    ├── volatility_algos.py       # 3 volatility algorithms
    ├── volume_algos.py           # 3 volume algorithms
    ├── statistical_algos.py      # 2 statistical algorithms
    ├── risk_sizing.py            # Position sizing calculations
    └── time_filters.py           # Session/time-of-day filters
```

## Called By

`engine.py` only — strategies never called directly by other modules.

## Algorithm Contract

Every algo returns `(signal: float, detail: str)`:
- `signal > 0` = bullish, `< 0` = bearish, `== 0` = neutral

## Conventions

- Register new algos in `signals.py` dispatcher
- Document algo params in `/docs/strategies/`
- Never read live prices inside an algo — accept candle arrays only
