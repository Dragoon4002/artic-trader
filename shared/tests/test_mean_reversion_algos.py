from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "app" / "strategies" / "quant_algos" / "mean_reversion_algos.py"
    spec = spec_from_file_location("mean_reversion_algos", module_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_stochastic_signal(candles, k_period=14, d_period=3):
    if not candles or len(candles) < k_period:
        return 0.0, f"warming up ({len(candles)}/{k_period})"
    high = max(c["high"] for c in candles[-k_period:])
    low = min(c["low"] for c in candles[-k_period:])
    close = candles[-1]["close"]
    if high == low:
        return 0.0, "flat range"
    k = 100 * (close - low) / (high - low)
    k_vals = []
    for i in range(len(candles) - k_period, len(candles)):
        h = max(c["high"] for c in candles[i - k_period + 1 : i + 1])
        l_ = min(c["low"] for c in candles[i - k_period + 1 : i + 1])
        c_ = candles[i]["close"]
        k_vals.append(100 * (c_ - l_) / (h - l_) if h != l_ else 50)
    d = sum(k_vals[-d_period:]) / d_period if len(k_vals) >= d_period else k
    if k <= 20:
        sig = 0.5
    elif k >= 80:
        sig = -0.5
    else:
        sig = (50 - k) / 50
    return max(-1, min(1, sig)), f"%K={k:.1f} %D={d:.1f}"


def make_candles(count=120):
    return [
        {
            "high": 100 + (i % 17) + i * 0.01,
            "low": 95 + (i % 11) + i * 0.01,
            "close": 97 + (i % 13) + i * 0.01,
        }
        for i in range(count)
    ]


def test_stochastic_signal_matches_previous_d_value():
    module = load_module()
    candles = make_candles()

    assert module.stochastic_signal(candles, k_period=14, d_period=3) == reference_stochastic_signal(
        candles, k_period=14, d_period=3
    )


def test_stochastic_signal_keeps_large_d_period_fallback():
    module = load_module()
    candles = make_candles()

    assert module.stochastic_signal(candles, k_period=14, d_period=20) == reference_stochastic_signal(
        candles, k_period=14, d_period=20
    )
