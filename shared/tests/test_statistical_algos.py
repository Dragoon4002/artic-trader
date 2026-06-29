import math

from app.strategies.quant_algos.statistical_algos import linear_regression_channel


def _legacy_linear_regression_channel(prices, lookback=20, num_std=2.0):
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


def test_linear_regression_channel_matches_legacy_outputs():
    prices = [
        100.0 + i * 0.37 + math.sin(i / 3.0) * 2.5 + (i % 7) * 0.11
        for i in range(240)
    ]

    for lookback in (5, 20, 55, 120):
        expected_signal, expected_detail = _legacy_linear_regression_channel(
            prices, lookback=lookback
        )
        signal, detail = linear_regression_channel(prices, lookback=lookback)

        assert math.isclose(signal, expected_signal, rel_tol=0, abs_tol=1e-10)
        assert detail == expected_detail


def test_linear_regression_channel_preserves_edge_cases():
    assert linear_regression_channel([1.0, 2.0], lookback=5) == (
        0.0,
        "warming up (2/5)",
    )
    assert linear_regression_channel([1.0, 2.0], lookback=1) == (0.0, "singular")
    assert linear_regression_channel([1.0, 2.0], lookback=0) == (0.0, "singular")
