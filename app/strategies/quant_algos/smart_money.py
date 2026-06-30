"""
Smart-money tracker.

Volume-confirmed breakout used as a proxy for whale-wallet accumulation:
- 24h volume > 2x rolling 7d average volume
- Close in top 25% of the current candle's range
- OBV trending up over the last 5 candles

Long-only. Stop = 1.5x ATR below entry, target = 3x ATR above entry.

TODO(mantle): replace volume-proxy heuristic with a real Mantle on-chain
whale-wallet feed. We expect a list of tracked wallets (top stETH/USDC LPs,
known market-maker hot wallets, treasury addresses) and a per-tick check
against their balance deltas + DEX inflow events. See
/docs/connections/onchain.md for the Mantle adapter plan; once landed, wire
that signal into the volume-multiple gate below and demote the volume check
to a tiebreaker.
"""
from typing import List, Tuple


def _atr(candles: List[dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    tr_list = []
    for i in range(1, len(candles)):
        h, l_ = candles[i]["high"], candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr_list.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
    return sum(tr_list[-period:]) / period if len(tr_list) >= period else 0.0


def _obv_trending_up(candles: List[dict], lookback: int) -> bool:
    obv_delta = 0.0
    for i in range(len(candles) - lookback, len(candles)):
        v = candles[i].get("volume", 0) or 0
        if candles[i]["close"] >= candles[i - 1]["close"]:
            obv_delta += v
        else:
            obv_delta -= v
    return obv_delta > 0


def smart_money(
    candles: List[dict],
    vol_mult: float = 2.0,
    avg_window: int = 7,
    obv_window: int = 5,
    close_top_frac: float = 0.25,
    **_,
) -> Tuple[float, str]:
    """Volume-confirmed breakout as smart-money proxy. Long-only.

    Returns (signal, detail). signal in [0, 1].
    Bearish branch returns 0 (this strategy doesn't short).
    """
    need = max(avg_window + 1, obv_window + 1, 15)
    if not candles or len(candles) < need:
        return 0.0, f"warming up ({len(candles) if candles else 0}/{need})"

    last = candles[-1]
    last_vol = last.get("volume", 0) or 0
    if last_vol <= 0:
        return 0.0, "no volume on last candle"

    avg_vol = sum((c.get("volume", 0) or 0) for c in candles[-(avg_window + 1):-1]) / avg_window
    if avg_vol <= 0:
        return 0.0, "zero avg volume"
    vol_ratio = last_vol / avg_vol

    high, low, close = last["high"], last["low"], last["close"]
    if high == low:
        return 0.0, "doji / flat candle"
    close_pos = (close - low) / (high - low)  # 0..1, 1 = at high

    obv_up = _obv_trending_up(candles, obv_window)

    vol_ok = vol_ratio >= vol_mult
    close_ok = close_pos >= (1.0 - close_top_frac)

    if not (vol_ok and close_ok and obv_up):
        return (
            0.0,
            f"no setup: vol_ratio={vol_ratio:.2f} close_pos={close_pos:.2f} obv_up={obv_up}",
        )

    atr = _atr(candles, period=14)
    if atr <= 0:
        return 0.0, "no ATR for stops"

    # Stop / target metadata embedded in detail (engine logs it).
    sl = close - 1.5 * atr
    tp = close + 3.0 * atr
    sig = min(1.0, 0.5 + (vol_ratio - vol_mult) * 0.25)
    return sig, (
        f"smart_money long: vol_ratio={vol_ratio:.2f} close_pos={close_pos:.2f} "
        f"obv_up=True ATR={atr:.4f} SL={sl:.4f} TP={tp:.4f}"
    )
