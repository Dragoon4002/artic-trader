"""
Strategy-specific signal computation.
Implements quant logic for each strategy type selected by the LLM.
Uses quant_algos library from arcgenesis-ai-engine.
"""
import math
from typing import List, Optional, Tuple, Deque
from collections import deque

from ..schemas import StrategyPlan, Candle
from .quant_algos import (
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
    z_score,
    bollinger_reversion,
    rsi_signal,
    stochastic_signal,
    range_sr,
    atr_breakout,
    bollinger_squeeze,
    keltner_bollinger,
    vwap_deviation,
    obv_trend,
    funding_bias_stub,
    linear_regression_channel,
    kalman_fair_value,
)


def _candles_to_dicts(candles: Optional[List[Candle]]) -> Optional[List[dict]]:
    """Convert List[Candle] to list of dicts for quant algos."""
    if not candles:
        return None
    return [
        {
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": getattr(c, "volume", 0) or 0,
        }
        for c in candles
    ]


def _prices_from_history(price_history: Deque[float]) -> List[float]:
    return list(price_history)


def compute_strategy_signal(
    strategy: str,
    plan: StrategyPlan,
    price_history: Deque[float],
    candles: Optional[List[Candle]] = None,
) -> Tuple[float, str]:
    """
    Compute trading signal based on the selected strategy.
    Uses quant algorithms from quant_algos package.

    Returns:
        (signal, detail): signal positive=bullish, negative=bearish; detail for logging.
    """
    strategy_lower = (strategy or "momentum").lower().strip()
    lookback = max(2, plan.lookback)
    prices = _prices_from_history(price_history)
    cdicts = _candles_to_dicts(candles)

    # Price-only algos (work with price_history)
    if strategy_lower == "momentum":
        return simple_momentum(prices, lookback=lookback)
    if strategy_lower == "dual_momentum":
        return dual_momentum(prices, short_lookback=lookback // 2, long_lookback=lookback)
    if strategy_lower == "breakout":
        return breakout(prices, period=lookback)
    if strategy_lower == "donchian_channel":
        return donchian_channel(prices, period=lookback)
    if strategy_lower == "ma_crossover":
        return ma_crossover(prices, fast=max(2, lookback // 2), slow=lookback)
    if strategy_lower == "ema_crossover":
        return ema_crossover(prices, fast=max(2, lookback // 2), slow=lookback)
    if strategy_lower == "macd_signal":
        return macd_signal(prices, fast=12, slow=26, signal_period=9)
    if strategy_lower == "z_score":
        return z_score(prices, lookback=lookback)
    if strategy_lower == "bollinger_reversion":
        return bollinger_reversion(prices, period=lookback)
    if strategy_lower == "rsi_signal":
        return rsi_signal(prices, period=min(14, lookback))
    if strategy_lower == "range_sr":
        return range_sr(prices, lookback=lookback)
    if strategy_lower == "bollinger_squeeze":
        return bollinger_squeeze(prices, period=lookback)
    if strategy_lower == "linear_regression_channel":
        return linear_regression_channel(prices, lookback=lookback)
    if strategy_lower == "kalman_fair_value":
        return kalman_fair_value(prices)

    # Candle-based algos (need OHLC)
    if cdicts and len(cdicts) >= lookback:
        if strategy_lower == "trend_following":
            return ma_crossover(prices, fast=max(2, lookback // 2), slow=lookback)
        if strategy_lower == "mean_reversion":
            return z_score(prices, lookback=lookback)
        if strategy_lower == "adx_filter":
            return adx_filter(cdicts, period=14, threshold=25.0)
        if strategy_lower == "supertrend":
            return supertrend(cdicts, period=14, mult=3.0)
        if strategy_lower == "ichimoku_signal":
            return ichimoku_signal(cdicts, tenkan=9, kijun=26, senkou=52)
        if strategy_lower == "stochastic_signal":
            return stochastic_signal(cdicts, k_period=min(14, lookback), d_period=3)
        if strategy_lower == "atr_breakout":
            return atr_breakout(cdicts, period=14, mult=1.5)
        if strategy_lower == "keltner_bollinger":
            return keltner_bollinger(cdicts, period=lookback)
        if strategy_lower == "vwap_deviation":
            return vwap_deviation(cdicts)
        if strategy_lower == "obv_trend":
            return obv_trend(cdicts, lookback=lookback)

    # Fallbacks that work with price_history only
    if strategy_lower == "trend_following":
        return _signal_trend_following(plan, candles, price_history)
    if strategy_lower == "mean_reversion":
        return _signal_mean_reversion(plan, candles, price_history)
    if strategy_lower == "funding_oi_filter":
        return _signal_funding_oi_filter(plan, price_history, candles)

    if strategy_lower == "demo_mode":
        return _signal_demo_mode(prices)

    # Default: momentum
    return simple_momentum(prices, lookback=lookback)


def _signal_demo_mode(prices: List[float]) -> Tuple[float, str]:
    """Reliable-fire strategy for demos. Triggers a signal every few ticks
    based on the most recent micro-momentum, regardless of strict thresholds.
    Sign of the last 3-tick delta determines side; magnitude is clamped so
    the supervisor still has room to override.

    Not for production — deliberately overtrades.
    """
    if len(prices) < 4:
        return 0.0, "demo: warming up"
    recent = prices[-4:]
    delta = recent[-1] - recent[0]
    if recent[0] == 0:
        return 0.0, "demo: zero base"
    bps = (delta / recent[0]) * 10_000
    # clamp to a small but non-zero signal so the engine takes action
    if bps == 0:
        sig = 0.6 if recent[-1] >= recent[-2] else -0.6
    else:
        sig = max(-1.0, min(1.0, bps))
        if abs(sig) < 0.4:
            sig = 0.4 if sig >= 0 else -0.4
    return sig, f"demo: {bps:+.2f} bps over 4 ticks"


def _signal_trend_following(
    plan: StrategyPlan,
    candles: Optional[List[Candle]],
    price_history: Deque[float],
) -> Tuple[float, str]:
    """Fallback trend following when quant algo not used."""
    lookback = max(2, plan.lookback)
    fast_len = max(1, lookback // 2)
    if candles and len(candles) >= lookback:
        closes = [c.close for c in candles[-lookback:]]
    else:
        prices = list(price_history)
        if len(prices) < lookback:
            return 0.0, f"warming up ({len(prices)}/{lookback} bars)"
        closes = prices[-lookback:]
    fast_ma = sum(closes[-fast_len:]) / fast_len
    slow_ma = sum(closes) / len(closes)
    if slow_ma == 0:
        return 0.0, "invalid slow MA"
    signal = (fast_ma - slow_ma) / slow_ma
    return signal, f"trend={signal:.4f} (fast_ma={fast_ma:.2f}, slow_ma={slow_ma:.2f})"


def _signal_mean_reversion(
    plan: StrategyPlan,
    candles: Optional[List[Candle]],
    price_history: Deque[float],
) -> Tuple[float, str]:
    """Fallback mean reversion when quant algo not used."""
    lookback = max(3, plan.lookback)
    if candles and len(candles) >= lookback:
        closes = [c.close for c in candles[-lookback:]]
    else:
        prices = list(price_history)
        if len(prices) < lookback:
            return 0.0, f"warming up ({len(prices)}/{lookback} bars)"
        closes = prices[-lookback:]
    mean = sum(closes) / len(closes)
    variance = sum((c - mean) ** 2 for c in closes) / len(closes)
    std = math.sqrt(variance) if variance > 0 else 1e-10
    z_score_val = (closes[-1] - mean) / std
    signal = -z_score_val
    return signal, f"z_score={z_score_val:.2f} (price={closes[-1]:.2f}, mean={mean:.2f}, std={std:.4f})"


def _signal_funding_oi_filter(
    plan: StrategyPlan,
    price_history: Deque[float],
    candles: Optional[List[Candle]] = None,
) -> Tuple[float, str]:
    """Funding/OI filter: momentum with optional funding bias."""
    signal, detail = simple_momentum(
        list(price_history), lookback=max(1, plan.lookback)
    )
    return signal, f"funding_oi_filter: {detail}"
