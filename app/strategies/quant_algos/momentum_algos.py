"""
Trend / momentum quant algorithms.
All return (signal, detail) with signal > 0 bullish, < 0 bearish.
"""
import math
from typing import List, Tuple, Optional, Deque
from collections import deque


def _closes(candles: List[dict]) -> List[float]:
    return [c["close"] for c in candles] if candles and isinstance(candles[0], dict) else list(candles)


def _atr(candles: List[dict], period: int = 14) -> Optional[float]:
    if not candles or len(candles) < period + 1:
        return None
    tr_list = []
    for i in range(1, len(candles)):
        h, l_ = candles[i]["high"], candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr_list.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
    return sum(tr_list[-period:]) / period if len(tr_list) >= period else None


def simple_momentum(
    prices: List[float], lookback: int = 10, **_
) -> Tuple[float, str]:
    """Return over lookback. Positive = bullish."""
    if len(prices) < lookback or lookback < 1:
        return 0.0, f"warming up ({len(prices)}/{lookback})"
    p0, p1 = prices[-lookback], prices[-1]
    if p0 == 0:
        return 0.0, "invalid price"
    sig = (p1 - p0) / p0
    return sig, f"momentum={sig:.4f} ({lookback} bars)"


def dual_momentum(
    prices: List[float], short_lookback: int = 5, long_lookback: int = 20, **_
) -> Tuple[float, str]:
    """Short-term vs long-term momentum; signal = short - long (normalized)."""
    if len(prices) < long_lookback:
        return 0.0, f"warming up ({len(prices)}/{long_lookback})"
    p = prices[-1]
    p_short = prices[-short_lookback] if len(prices) >= short_lookback else prices[0]
    p_long = prices[-long_lookback]
    if p_long == 0:
        return 0.0, "invalid"
    mom_short = (p - p_short) / p_long
    mom_long = (p - p_long) / p_long
    sig = mom_short - mom_long
    return sig, f"dual_mom short={mom_short:.4f} long={mom_long:.4f}"


def breakout(
    prices: List[float], period: int = 20, **_
) -> Tuple[float, str]:
    """Entry when price breaks N-period high (bullish) or low (bearish)."""
    if len(prices) < period + 1:
        return 0.0, f"warming up ({len(prices)}/{period+1})"
    window = prices[-period-1:-1]  # exclude current
    high, low = max(window), min(window)
    p = prices[-1]
    if p > high:
        return 1.0, f"breakout above {period}-period high {high:.2f}"
    if p < low:
        return -1.0, f"breakout below {period}-period low {low:.2f}"
    return 0.0, f"inside range [{low:.2f},{high:.2f}]"


def donchian_channel(
    prices: List[float], period: int = 20, **_
) -> Tuple[float, str]:
    """Break of Donchian channel (e.g. 20 or 55). Similar to breakout."""
    if len(prices) < period:
        return 0.0, f"warming up ({len(prices)}/{period})"
    window = prices[-period:]
    high, low = max(window), min(window)
    p = prices[-1]
    mid = (high + low) / 2
    if mid == 0:
        return 0.0, "invalid"
    # Normalized position: (p - mid) / (high - low)
    if high == low:
        return 0.0, "flat channel"
    sig = (p - mid) / (high - low)
    return max(-1, min(1, sig)), f"donchian p={p:.2f} mid={mid:.2f}"


def ma_crossover(
    prices: List[float], fast: int = 10, slow: int = 20, **_
) -> Tuple[float, str]:
    """SMA crossover. Signal = (fast_ma - slow_ma) / slow_ma."""
    if len(prices) < slow:
        return 0.0, f"warming up ({len(prices)}/{slow})"
    fast_ma = sum(prices[-fast:]) / fast
    slow_ma = sum(prices[-slow:]) / slow
    if slow_ma == 0:
        return 0.0, "invalid"
    sig = (fast_ma - slow_ma) / slow_ma
    return sig, f"MA cross fast={fast_ma:.2f} slow={slow_ma:.2f}"


def _ema(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(prices[-period:]) / period
    for i in range(-period + 1, 0):
        ema = prices[i] * k + ema * (1 - k)
    return ema


def ema_crossover(
    prices: List[float], fast: int = 9, slow: int = 21, **_
) -> Tuple[float, str]:
    """EMA crossover (e.g. 9/21 or 12/26)."""
    if len(prices) < slow:
        return 0.0, f"warming up ({len(prices)}/{slow})"
    e_fast = _ema(prices, fast)
    e_slow = _ema(prices, slow)
    if e_fast is None or e_slow is None or e_slow == 0:
        return 0.0, "invalid"
    sig = (e_fast - e_slow) / e_slow
    return sig, f"EMA cross fast={e_fast:.2f} slow={e_slow:.2f}"


def macd_signal(
    prices: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9, **_
) -> Tuple[float, str]:
    """MACD line vs signal line. Signal = (macd - signal_line) normalized."""
    if len(prices) < slow + signal_period:
        return 0.0, f"warming up ({len(prices)}/{slow+signal_period})"
    # EMA fast and slow
    def ema_series(data: List[float], period: int) -> List[float]:
        k = 2 / (period + 1)
        out = []
        ema = sum(data[:period]) / period
        out.append(ema)
        for i in range(period, len(data)):
            ema = data[i] * k + ema * (1 - k)
            out.append(ema)
        return out
    ema_f = ema_series(prices, fast)
    ema_s = ema_series(prices, slow)
    # Align EMAs: ema_s index j = price index j+slow-1; ema_f index j+slow-fast = same price
    macd_line = [ema_f[j + slow - fast] - ema_s[j] for j in range(len(ema_s))]
    if len(macd_line) < signal_period:
        return 0.0, "macd warmup"
    sig_ema = sum(macd_line[-signal_period:]) / signal_period  # simplified signal line
    macd_val = macd_line[-1]
    diff = macd_val - sig_ema
    # Normalize by recent price for scale
    scale = prices[-1] * 0.01 if prices[-1] else 1
    sig = diff / scale if scale else 0
    return max(-1, min(1, sig)), f"MACD={macd_val:.4f} signal={sig_ema:.4f}"


def adx_filter(
    candles: List[dict], period: int = 14, threshold: float = 25.0, **_
) -> Tuple[float, str]:
    """ADX > threshold = trending (1), else ranging (0). Use as filter, not direction."""
    if not candles or len(candles) < period * 2:
        return 0.0, f"warming up ({len(candles)}/{period*2})"
    # Simplified ADX: use +DM -DM from high/low/close
    plus_dm = []
    minus_dm = []
    tr_list = []
    for i in range(1, len(candles)):
        h, l_, c = candles[i]["high"], candles[i]["low"], candles[i]["close"]
        pc = candles[i - 1]["close"]
        tr_list.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
        up = h - candles[i - 1]["high"]
        down = candles[i - 1]["low"] - l_
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
    # Smooth and compute +DI -DI then ADX (simplified)
    n = period
    if len(tr_list) < n:
        return 0.0, "insufficient data"
    atr = sum(tr_list[-n:]) / n
    plus_di = 100 * sum(plus_dm[-n:]) / n / atr if atr else 0
    minus_di = 100 * sum(minus_dm[-n:]) / n / atr if atr else 0
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) else 0
    # Return 1 if trending else 0 (filter)
    sig = 1.0 if dx >= threshold else 0.0
    return sig, f"ADX={dx:.1f} (threshold={threshold})"


def supertrend(
    candles: List[dict], period: int = 14, mult: float = 3.0, **_
) -> Tuple[float, str]:
    """ATR-based trend line. Long when price > supertrend, short when below."""
    if not candles or len(candles) < period + 1:
        return 0.0, f"warming up ({len(candles)}/{period+1})"
    atr_val = _atr(candles, period)
    if atr_val is None or atr_val <= 0:
        return 0.0, "no ATR"
    hl2 = (candles[-1]["high"] + candles[-1]["low"]) / 2
    upper = hl2 + mult * atr_val
    lower = hl2 - mult * atr_val
    close = candles[-1]["close"]
    # Simplified: compare close to upper/lower band
    if close > upper:
        return 1.0, f"supertrend long close={close:.2f} > upper={upper:.2f}"
    if close < lower:
        return -1.0, f"supertrend short close={close:.2f} < lower={lower:.2f}"
    return 0.0, f"inside band [{lower:.2f},{upper:.2f}]"


def ichimoku_signal(
    candles: List[dict], tenkan: int = 9, kijun: int = 26, senkou: int = 52, **_
) -> Tuple[float, str]:
    """Ichimoku: Tenkan/Kijun cross and price vs cloud. Simplified."""
    if not candles or len(candles) < senkou:
        return 0.0, f"warming up ({len(candles)}/{senkou})"
    def mid(cs):
        return (max(c["high"] for c in cs) + min(c["low"] for c in cs)) / 2
    tenkan_val = mid(candles[-tenkan:])
    kijun_val = mid(candles[-kijun:])
    close = candles[-1]["close"]
    # Tenkan cross Kijun
    if tenkan_val > kijun_val:
        cross = 1.0
    elif tenkan_val < kijun_val:
        cross = -1.0
    else:
        cross = 0.0
    # Price vs Kijun
    if close > kijun_val:
        sig = 0.5 + 0.5 * cross
    else:
        sig = -0.5 + 0.5 * cross
    return max(-1, min(1, sig)), f"tenkan={tenkan_val:.2f} kijun={kijun_val:.2f} close={close:.2f}"
