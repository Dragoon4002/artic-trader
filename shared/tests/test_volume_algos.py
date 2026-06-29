from app.strategies.quant_algos.volume_algos import obv_trend


def _legacy_obv_trend(candles, lookback=10):
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
    sig = max(-1, min(1, change_pct * 10))
    return sig, f"OBV change%={change_pct:.4f}"


def _candles(count):
    price = 100.0
    out = []
    for i in range(count):
        step = ((i % 9) - 4) * 0.17 + (0.31 if i % 13 == 0 else -0.08)
        price = max(1.0, price + step)
        out.append(
            {
                "high": price + 0.8 + (i % 5) * 0.03,
                "low": price - 0.7,
                "close": price,
                "volume": 100 + (i * 37) % 850,
            }
        )
    return out


def test_obv_trend_matches_legacy_outputs():
    candles = _candles(5000)

    for lookback in (2, 5, 10, 55, 250, 1000):
        assert obv_trend(candles, lookback=lookback) == _legacy_obv_trend(
            candles, lookback=lookback
        )


def test_obv_trend_preserves_edge_cases():
    assert obv_trend(_candles(3), lookback=10) == (0.0, "warming up (3/11)")

    flat_prev = [
        {"close": 100, "volume": 0},
        {"close": 101, "volume": 0},
        {"close": 102, "volume": 100},
        {"close": 103, "volume": 100},
    ]
    assert obv_trend(flat_prev, lookback=2) == (0.0, "obv_prev zero")
