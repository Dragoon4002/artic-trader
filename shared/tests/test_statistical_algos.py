import math

from app.strategies.quant_algos.statistical_algos import linear_regression_channel


def _previous_linear_regression_channel(prices, lookback=20):
    if len(prices) < lookback:
        return 0.0, f"warming up ({len(prices)}/{lookback})"
    x = list(range(lookback))
    y = prices[-lookback:]
    n = len(x)
    sx, sy = sum(x), sum(y)
    sxx = sum(xi * xi for xi in x)
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    den = n * sxx - sx * sx
    if den == 0:
        return 0.0, "singular"
    slope = (n * sxy - sx * sy) / den
    intercept = (sy - slope * sx) / n
    pred = intercept + slope * (n - 1)
    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, y)]
    var = sum(r * r for r in residuals) / len(residuals)
    std = math.sqrt(var) if var > 0 else 1e-10
    p = prices[-1]
    dev = (p - pred) / std if std else 0
    sig = -dev
    return max(-2, min(2, sig)), f"dev={dev:.2f} pred={pred:.2f}"


def test_linear_regression_channel_matches_previous_outputs():
    cases = [
        [100 + i * 0.2 for i in range(80)],
        [100 + math.sin(i / 3) * 2 + i * 0.03 for i in range(80)],
        [120 - i * 0.35 + math.cos(i / 4) for i in range(80)],
        [100, 102, 101, 103, 99, 98, 100, 101, 103, 104, 102, 101],
    ]

    for prices in cases:
        expected_signal, expected_detail = _previous_linear_regression_channel(
            prices, lookback=min(20, len(prices))
        )
        actual_signal, actual_detail = linear_regression_channel(
            prices, lookback=min(20, len(prices))
        )

        assert actual_signal == expected_signal
        assert actual_detail == expected_detail


def test_linear_regression_channel_keeps_warmup_behavior():
    assert linear_regression_channel([1.0, 2.0, 3.0], lookback=5) == (
        0.0,
        "warming up (3/5)",
    )
