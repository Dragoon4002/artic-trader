from importlib import import_module

from app.strategies.quant_algos import momentum_algos, risk_sizing, volatility_algos


smart_money = import_module("app.strategies.quant_algos.smart_money")


def _candles(count):
    out = []
    for i in range(count):
        close = 100 + ((i * 7) % 31) + (i * 0.02)
        high = close + 1.5 + ((i * 3) % 5) * 0.1
        low = close - 1.2 - ((i * 5) % 7) * 0.1
        out.append({"high": high, "low": low, "close": close, "volume": 1000 + i})
    return out


def _legacy_atr(candles, period=14, none_on_warmup=True):
    if not candles or len(candles) < period + 1:
        return None if none_on_warmup else 0.0
    tr_list = []
    for i in range(1, len(candles)):
        h, l_ = candles[i]["high"], candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr_list.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
    fallback = None if none_on_warmup else 0.0
    return sum(tr_list[-period:]) / period if len(tr_list) >= period else fallback


def _legacy_adx_filter(candles, period=14, threshold=25.0):
    if not candles or len(candles) < period * 2:
        return 0.0, f"warming up ({len(candles)}/{period*2})"
    plus_dm = []
    minus_dm = []
    tr_list = []
    for i in range(1, len(candles)):
        h, l_ = candles[i]["high"], candles[i]["low"]
        pc = candles[i - 1]["close"]
        tr_list.append(max(h - l_, abs(h - pc), abs(l_ - pc)))
        up = h - candles[i - 1]["high"]
        down = candles[i - 1]["low"] - l_
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
    n = period
    if len(tr_list) < n:
        return 0.0, "insufficient data"
    atr = sum(tr_list[-n:]) / n
    plus_di = 100 * sum(plus_dm[-n:]) / n / atr if atr else 0
    minus_di = 100 * sum(minus_dm[-n:]) / n / atr if atr else 0
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) else 0
    sig = 1.0 if dx >= threshold else 0.0
    return sig, f"ADX={dx:.1f} (threshold={threshold})"


def test_atr_helpers_match_legacy_tail_result_on_long_history():
    candles = _candles(5000)

    assert risk_sizing._atr(candles, period=14) == _legacy_atr(candles, period=14)
    assert volatility_algos._atr(candles, period=14) == _legacy_atr(candles, period=14)
    assert momentum_algos._atr(candles, period=14) == _legacy_atr(candles, period=14)
    assert smart_money._atr(candles, period=14) == _legacy_atr(
        candles, period=14, none_on_warmup=False
    )


def test_adx_filter_matches_legacy_tail_result_on_long_history():
    candles = _candles(5000)

    assert momentum_algos.adx_filter(candles, period=14) == _legacy_adx_filter(
        candles, period=14
    )


def test_atr_helpers_keep_warmup_contracts():
    candles = _candles(4)

    assert risk_sizing._atr(candles, period=14) is None
    assert volatility_algos._atr(candles, period=14) is None
    assert momentum_algos._atr(candles, period=14) is None
    assert smart_money._atr(candles, period=14) == 0.0
