import math

from app.strategies.quant_algos.momentum_algos import macd_signal


def _legacy_macd_signal(prices, fast=12, slow=26, signal_period=9):
    if len(prices) < slow + signal_period:
        return 0.0, f"warming up ({len(prices)}/{slow+signal_period})"

    def ema_series(data, period):
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
    macd_line = [ema_f[j + slow - fast] - ema_s[j] for j in range(len(ema_s))]
    if len(macd_line) < signal_period:
        return 0.0, "macd warmup"
    sig_ema = sum(macd_line[-signal_period:]) / signal_period
    macd_val = macd_line[-1]
    diff = macd_val - sig_ema
    scale = prices[-1] * 0.01 if prices[-1] else 1
    sig = diff / scale if scale else 0
    return max(-1, min(1, sig)), f"MACD={macd_val:.4f} signal={sig_ema:.4f}"


def _prices(count):
    out = []
    price = 100.0
    for i in range(count):
        drift = 0.08 + math.sin(i / 11.0) * 0.55 + ((i % 17) - 8) * 0.013
        price = max(1.0, price + drift)
        out.append(price)
    return out


def test_macd_signal_matches_legacy_outputs():
    prices = _prices(5000)

    for params in (
        {},
        {"fast": 5, "slow": 13, "signal_period": 4},
        {"fast": 8, "slow": 21, "signal_period": 7},
        {"fast": 12, "slow": 55, "signal_period": 18},
    ):
        assert macd_signal(prices, **params) == _legacy_macd_signal(prices, **params)


def test_macd_signal_preserves_edge_cases():
    assert macd_signal(_prices(20)) == (0.0, "warming up (20/35)")

    zero_scale_prices = _prices(80)
    zero_scale_prices[-1] = 0.0
    assert macd_signal(zero_scale_prices) == _legacy_macd_signal(zero_scale_prices)
