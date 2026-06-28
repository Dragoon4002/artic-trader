from app.strategies.quant_algos.mean_reversion_algos import rsi_signal


def _legacy_rsi_signal(prices, period=14, overbought=70, oversold=30):
    if len(prices) < period + 1:
        return 0.0, f"warming up ({len(prices)}/{period+1})"
    gains, losses = [], []
    for i in range(1, len(prices)):
        ch = prices[i] - prices[i - 1]
        gains.append(ch if ch > 0 else 0)
        losses.append(-ch if ch < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    if rsi <= oversold:
        sig = 0.5
    elif rsi >= overbought:
        sig = -0.5
    else:
        sig = (50 - rsi) / 50
    return max(-1, min(1, sig)), f"RSI={rsi:.1f}"


def test_rsi_signal_matches_legacy_result_on_long_history():
    prices = [100 + ((i * 17) % 23) - ((i * 5) % 11) + (i * 0.01) for i in range(5000)]

    assert rsi_signal(prices, period=14) == _legacy_rsi_signal(prices, period=14)


def test_rsi_signal_keeps_warmup_message():
    assert rsi_signal([100.0, 101.0], period=14) == (0.0, "warming up (2/15)")
