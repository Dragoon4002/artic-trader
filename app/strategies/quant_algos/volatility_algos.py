"""
Volatility-based quant algorithms.
"""
import math
from typing import List, Tuple, Optional


def _atr(candles: List[dict], period: int = 14) -> Optional[float]:
    if not candles or len(candles) < period + 1:
        return None
    tr_list = []
    for i in range(1, len(candles)):
        h, l_ = candles[i]["high"], candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr_list.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
    return sum(tr_list[-period:]) / period if len(tr_list) >= period else None


def atr_breakout(
    candles: List[dict], period: int = 14, mult: float = 1.5, **_
) -> Tuple[float, str]:
    """Entry when range expands vs ATR (volatility breakout)."""
    if not candles or len(candles) < period + 1:
        return 0.0, f"warming up ({len(candles)}/{period+1})"
    atr_val = _atr(candles, period)
    if atr_val is None or atr_val <= 0:
        return 0.0, "no ATR"
    recent_range = candles[-1]["high"] - candles[-1]["low"]
    # Expand vs average
    if recent_range > atr_val * mult:
        # Bullish if close near high
        close, high, low = candles[-1]["close"], candles[-1]["high"], candles[-1]["low"]
        if high == low:
            return 0.0, "doji"
        pos = (close - low) / (high - low)
        sig = 1.0 if pos > 0.5 else -1.0
        return sig, f"ATR breakout range={recent_range:.2f} ATR={atr_val:.2f}"
    return 0.0, f"range={recent_range:.2f} < ATR*{mult}"


def bollinger_squeeze(
    prices: List[float], period: int = 20, width_pct: float = 0.1, **_
) -> Tuple[float, str]:
    """Low vol (narrow bands) then breakout. Signal when width expands from low."""
    if len(prices) < period * 2:
        return 0.0, f"warming up ({len(prices)}/{period*2})"
    window = prices[-period:]
    mean = sum(window) / len(window)
    var = sum((x - mean) ** 2 for x in window) / len(window)
    std = math.sqrt(var) if var > 0 else 1e-10
    width = (2 * std) / mean if mean else 0
    # Compare to previous period width
    prev_window = prices[-period * 2 : -period]
    prev_mean = sum(prev_window) / len(prev_window)
    prev_var = sum((x - prev_mean) ** 2 for x in prev_window) / len(prev_window)
    prev_std = math.sqrt(prev_var) if prev_var > 0 else 1e-10
    prev_width = (2 * prev_std) / prev_mean if prev_mean else 0
    # Squeeze: width was low and now expanding; direction from price vs mean
    if prev_width > 0 and width > prev_width * (1 + width_pct):
        sig = 1.0 if prices[-1] > mean else -1.0
        return sig, f"squeeze breakout width={width:.4f} prev={prev_width:.4f}"
    return 0.0, f"width={width:.4f} no squeeze"


def keltner_bollinger(
    candles: List[dict], period: int = 20, bb_std: float = 2.0, kc_mult: float = 2.0, **_
) -> Tuple[float, str]:
    """Keltner (ATR) vs Bollinger bands. Trade break or reversion."""
    if not candles or len(candles) < period + 1:
        return 0.0, f"warming up ({len(candles)}/{period+1})"
    closes = [c["close"] for c in candles[-period:]]
    mean = sum(closes) / len(closes)
    var = sum((x - mean) ** 2 for x in closes) / len(closes)
    std = math.sqrt(var) if var > 0 else 1e-10
    atr_val = _atr(candles, 14)
    if atr_val is None:
        atr_val = std
    kc_upper = mean + kc_mult * atr_val
    kc_lower = mean - kc_mult * atr_val
    bb_upper = mean + bb_std * std
    bb_lower = mean - bb_std * std
    p = candles[-1]["close"]
    # Reversion: price outside Keltner -> fade
    if p >= kc_upper:
        return -0.5, f"price above Keltner upper {kc_upper:.2f}"
    if p <= kc_lower:
        return 0.5, f"price below Keltner lower {kc_lower:.2f}"
    return 0.0, f"inside Keltner [{kc_lower:.2f},{kc_upper:.2f}]"
