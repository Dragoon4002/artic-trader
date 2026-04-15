"""
Risk / position sizing (multipliers or size, not direction).
"""
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


def kelly_size(
    win_rate: float, win_loss_ratio: float, fraction: float = 0.25, **_
) -> Tuple[float, str]:
    """Kelly fraction for position size. Returns (fraction, detail). Use as multiplier 0..1."""
    if win_rate <= 0 or win_rate >= 1:
        return 0.0, "invalid win_rate"
    # kelly = W - (1-W)/R where R = win/loss ratio
    kelly = win_rate - (1 - win_rate) / win_loss_ratio
    kelly = max(0, min(1, kelly))
    frac = kelly * fraction
    return frac, f"kelly={kelly:.3f} frac={frac:.3f} (W={win_rate} R={win_loss_ratio})"


def vol_scaling_mult(
    candles: List[dict], target_vol: float = 0.2, period: int = 14, **_
) -> Tuple[float, str]:
    """Scale size by inverse of recent vol (ATR). Return multiplier (e.g. 0.5 = half size)."""
    if not candles or len(candles) < period + 1:
        return 1.0, "insufficient data"
    atr_val = _atr(candles, period)
    if atr_val is None or atr_val <= 0:
        return 1.0, "no ATR"
    close = candles[-1]["close"]
    if close <= 0:
        return 1.0, "invalid price"
    current_vol = atr_val / close
    if current_vol <= 0:
        return 1.0, "zero vol"
    mult = target_vol / current_vol
    mult = max(0.25, min(2.0, mult))
    return mult, f"vol_scale={mult:.2f} (target={target_vol} current={current_vol:.4f})"
