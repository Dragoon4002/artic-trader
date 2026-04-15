"""
Volume / order flow quant algorithms (require volume in candles).
"""
from typing import List, Tuple, Optional


def vwap_deviation(
    candles: List[dict], **_
) -> Tuple[float, str]:
    """Trade around VWAP. Signal = (price - vwap) / vwap. Negative = below VWAP (long bias)."""
    if not candles or not candles[0].get("volume"):
        return 0.0, "no volume data"
    cum_pv = 0.0
    cum_vol = 0.0
    for c in candles:
        v = c.get("volume", 0)
        typical = (c["high"] + c["low"] + c["close"]) / 3
        cum_pv += typical * v
        cum_vol += v
    if cum_vol <= 0:
        return 0.0, "zero volume"
    vwap = cum_pv / cum_vol
    p = candles[-1]["close"]
    if vwap == 0:
        return 0.0, "invalid vwap"
    sig = -(p - vwap) / vwap  # below vwap -> positive (buy)
    return max(-1, min(1, sig)), f"p={p:.2f} vwap={vwap:.2f}"


def obv_trend(
    candles: List[dict], lookback: int = 10, **_
) -> Tuple[float, str]:
    """OBV trend: volume-confirmed momentum. Signal from OBV change over lookback."""
    if not candles or len(candles) < lookback + 1:
        return 0.0, f"warming up ({len(candles)}/{lookback+1})"
    obv = 0
    for i in range(1, len(candles)):
        v = candles[i].get("volume", 0)
        if candles[i]["close"] >= candles[i - 1]["close"]:
            obv += v
        else:
            obv -= v
    obv_prev = 0
    for i in range(1, len(candles) - lookback):
        v = candles[i].get("volume", 0)
        if candles[i]["close"] >= candles[i - 1]["close"]:
            obv_prev += v
        else:
            obv_prev -= v
    if obv_prev == 0:
        return 0.0, "obv_prev zero"
    change_pct = (obv - obv_prev) / abs(obv_prev)
    sig = max(-1, min(1, change_pct * 10))  # scale
    return sig, f"OBV change%={change_pct:.4f}"


def funding_bias_stub(
    prices: List[float], funding_rate: Optional[float] = None, **_
) -> Tuple[float, str]:
    """Stub: fade extreme funding (high positive funding -> short bias). Requires funding data."""
    if funding_rate is None:
        return 0.0, "no funding data (stub)"
    if funding_rate > 0.0005:
        return -0.3, f"high funding {funding_rate:.4f} -> short bias"
    if funding_rate < -0.0005:
        return 0.3, f"low funding {funding_rate:.4f} -> long bias"
    return 0.0, f"neutral funding {funding_rate:.4f}"
