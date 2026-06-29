"""
Statistical / ML-adjacent quant algorithms.
"""
import math
from typing import List, Tuple, Optional


def linear_regression_channel(
    prices: List[float], lookback: int = 20, num_std: float = 2.0, **_
) -> Tuple[float, str]:
    """Deviation from linear regression line. Trade reversion to line."""
    if len(prices) < lookback:
        return 0.0, f"warming up ({len(prices)}/{lookback})"
    y = prices[-lookback:]
    n = lookback
    sx = n * (n - 1) // 2
    sxx = n * (n - 1) * (2 * n - 1) // 6
    sy = sum(y)
    sxy = sum(xi * yi for xi, yi in enumerate(y))
    den = n * sxx - sx * sx
    if den == 0:
        return 0.0, "singular"
    slope = (n * sxy - sx * sy) / den
    intercept = (sy - slope * sx) / n
    pred = intercept + slope * (n - 1)
    residual_sum_sq = 0.0
    for xi, yi in enumerate(y):
        residual = yi - (intercept + slope * xi)
        residual_sum_sq += residual * residual
    var = residual_sum_sq / n
    std = math.sqrt(var) if var > 0 else 1e-10
    p = prices[-1]
    dev = (p - pred) / std if std else 0
    sig = -dev  # revert to line
    return max(-2, min(2, sig)), f"dev={dev:.2f} pred={pred:.2f}"


def kalman_fair_value(
    prices: List[float], process_var: float = 0.01, measure_var: float = 0.1, **_
) -> Tuple[float, str]:
    """Simple 1D Kalman filter for fair value. Signal = (price - fair_value) / scale."""
    if len(prices) < 5:
        return 0.0, f"warming up ({len(prices)}/5)"
    # 1D Kalman: state = price estimate, P = variance
    x = prices[0]
    P = 1.0
    Q, R = process_var, measure_var
    for z in prices[1:]:
        x_pred = x
        P_pred = P + Q
        K = P_pred / (P_pred + R)
        x = x_pred + K * (z - x_pred)
        P = (1 - K) * P_pred
    fair = x
    p = prices[-1]
    scale = max(P, 1e-6) ** 0.5
    sig = -(p - fair) / scale if scale else 0
    return max(-2, min(2, sig)), f"fair={fair:.2f} p={p:.2f}"
