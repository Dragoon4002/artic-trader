"""
Quant algorithm library for BNB AI Engine.
Each module exposes signal functions: (prices/candles, **params) -> (signal, detail).
Signal: positive = bullish, negative = bearish, 0 = neutral.
"""

from .momentum_algos import (
    simple_momentum,
    dual_momentum,
    breakout,
    donchian_channel,
    ma_crossover,
    ema_crossover,
    macd_signal,
    adx_filter,
    supertrend,
    ichimoku_signal,
)
from .mean_reversion_algos import (
    z_score,
    bollinger_reversion,
    rsi_signal,
    stochastic_signal,
    range_sr,
)
from .volatility_algos import (
    atr_breakout,
    bollinger_squeeze,
    keltner_bollinger,
)
from .volume_algos import (
    vwap_deviation,
    obv_trend,
    funding_bias_stub,
)
from .statistical_algos import (
    linear_regression_channel,
    kalman_fair_value,
)
from .risk_sizing import (
    kelly_size,
    vol_scaling_mult,
)
from .time_filters import (
    session_filter,
    day_of_week_filter,
)

__all__ = [
    "simple_momentum",
    "dual_momentum",
    "breakout",
    "donchian_channel",
    "ma_crossover",
    "ema_crossover",
    "macd_signal",
    "adx_filter",
    "supertrend",
    "ichimoku_signal",
    "z_score",
    "bollinger_reversion",
    "rsi_signal",
    "stochastic_signal",
    "range_sr",
    "atr_breakout",
    "bollinger_squeeze",
    "keltner_bollinger",
    "vwap_deviation",
    "obv_trend",
    "funding_bias_stub",
    "linear_regression_channel",
    "kalman_fair_value",
    "kelly_size",
    "vol_scaling_mult",
    "session_filter",
    "day_of_week_filter",
]
