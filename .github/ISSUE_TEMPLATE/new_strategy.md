---
name: New strategy proposal
about: Propose a new quantitative trading algorithm
labels: strategy
---

## Strategy Name

<!-- snake_case name that will be used in code, e.g. `hull_moving_average` -->

## Category

- [ ] Momentum
- [ ] Mean Reversion
- [ ] Volatility
- [ ] Volume
- [ ] Statistical
- [ ] Other: ___

## Description

<!-- What market condition or edge does this strategy exploit? -->

## Signal Logic

<!-- Describe the algorithm in plain English. Include:
     - What indicators / data points it uses
     - What conditions trigger a long signal (close to +1.0)
     - What conditions trigger a short signal (close to -1.0)
     - What conditions produce flat (0.0)
     - Minimum candle history required -->

## Parameters

<!-- List any configurable params with types and defaults, e.g.:
     - `period: int = 20`
     - `std_dev_multiplier: float = 2.0` -->

## References

<!-- Paper, article, or book where this strategy is described (if any) -->

## Backtest Results (optional)

<!-- If you've backtested this, share the results — win rate, Sharpe ratio, drawdown, timeframe, symbol -->

## Are you implementing this?

- [ ] Yes, I'll open a PR with the implementation + tests
- [ ] I'm proposing it for someone else to implement
