"""
Mean reversion / range quant algorithms.
"""
import math
from typing import List, Tuple, Optional


def _closes(candles) -> List[float]:
    if not candles:
        return []
    if isinstance(candles[0], dict):
        return [c["close"] for c in candles]
    return list(candles)


def z_score(
    prices: List[float], lookback: int = 20, **_
) -> Tuple[float, str]:
    """Z-score of price vs rolling mean. Inverted: oversold -> positive (long)."""
    if len(prices) < lookback:
        return 0.0, f"warming up ({len(prices)}/{lookback})"
    window = prices[-lookback:]
    mean = sum(window) / len(window)
    var = sum((x - mean) ** 2 for x in window) / len(window)
    std = math.sqrt(var) if var > 0 else 1e-10
    z = (prices[-1] - mean) / std
    sig = -z  # oversold (negative z) -> positive signal
    return max(-2, min(2, sig)), f"z={z:.2f} mean={mean:.2f} std={std:.4f}"


def bollinger_reversion(
    prices: List[float], period: int = 20, num_std: float = 2.0, **_
) -> Tuple[float, str]:
    """Reversion to middle band. (price - mid) / (upper - mid) inverted."""
    if len(prices) < period:
        return 0.0, f"warming up ({len(prices)}/{period})"
    window = prices[-period:]
    mean = sum(window) / len(window)
    var = sum((x - mean) ** 2 for x in window) / len(window)
    std = math.sqrt(var) if var > 0 else 1e-10
    upper = mean + num_std * std
    lower = mean - num_std * std
    p = prices[-1]
    if upper == lower:
        return 0.0, "flat bands"
    # Position within band: -1 at lower, +1 at upper. Reversion: invert.
    pos = (p - mean) / (num_std * std) if std else 0
    sig = -pos
    return max(-1, min(1, sig)), f"p={p:.2f} mid={mean:.2f} upper={upper:.2f} lower={lower:.2f}"


def rsi_signal(
    prices: List[float], period: int = 14, overbought: float = 70, oversold: float = 30, **_
) -> Tuple[float, str]:
    """RSI. Oversold (< 30) -> positive, overbought (> 70) -> negative."""
    if len(prices) < period + 1:
        return 0.0, f"warming up ({len(prices)}/{period+1})"
    gains, losses = [], []
    for i in range(1, len(prices)):
        ch = prices[i] - prices[i - 1]
        gains.append(ch if ch > 0 else 0)
        losses.append(-ch if ch < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    if rsi <= oversold:
        sig = 0.5
    elif rsi >= overbought:
        sig = -0.5
    else:
        sig = (50 - rsi) / 50  # neutral at 50
    return max(-1, min(1, sig)), f"RSI={rsi:.1f}"


def stochastic_signal(
    candles: List[dict], k_period: int = 14, d_period: int = 3, **_
) -> Tuple[float, str]:
    """Stochastic %K/%D. Oversold -> long, overbought -> short."""
    if not candles or len(candles) < k_period:
        return 0.0, f"warming up ({len(candles)}/{k_period})"
    high = max(c["high"] for c in candles[-k_period:])
    low = min(c["low"] for c in candles[-k_period:])
    close = candles[-1]["close"]
    if high == low:
        return 0.0, "flat range"
    k = 100 * (close - low) / (high - low)
    # Simplified %D = SMA of %K
    k_vals = []
    for i in range(len(candles) - k_period, len(candles)):
        h = max(c["high"] for c in candles[i - k_period + 1 : i + 1])
        l_ = min(c["low"] for c in candles[i - k_period + 1 : i + 1])
        c_ = candles[i]["close"]
        k_vals.append(100 * (c_ - l_) / (h - l_) if h != l_ else 50)
    d = sum(k_vals[-d_period:]) / d_period if len(k_vals) >= d_period else k
    if k <= 20:
        sig = 0.5
    elif k >= 80:
        sig = -0.5
    else:
        sig = (50 - k) / 50
    return max(-1, min(1, sig)), f"%K={k:.1f} %D={d:.1f}"


def range_sr(
    prices: List[float], lookback: int = 20, **_
) -> Tuple[float, str]:
    """Fade at recent high/low as S/R. Price near high -> short bias, near low -> long."""
    if len(prices) < lookback:
        return 0.0, f"warming up ({len(prices)}/{lookback})"
    window = prices[-lookback:]
    high, low = max(window), min(window)
    p = prices[-1]
    if high == low:
        return 0.0, "flat range"
    # 0 at low, 1 at high. Fade: long near low, short near high
    pos = (p - low) / (high - low)
    sig = 0.5 - pos  # long when pos<0.5, short when pos>0.5
    return max(-1, min(1, sig)), f"p={p:.2f} range=[{low:.2f},{high:.2f}]"
