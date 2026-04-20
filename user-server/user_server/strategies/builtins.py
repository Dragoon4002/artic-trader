"""Minimal built-in strategies. Used as the universal fallback.

Full built-in catalog lives in app.strategies (agent container); this module
holds only what the sandbox fallback needs. A8 wires `app.strategies` via
`pip install -e /app` so user-server can load the full set lazily.
"""
from __future__ import annotations

from typing import Callable

Signal = tuple[float, str]  # (score in [-1, 1], reason)


def simple_momentum(plan: dict, price_history: list[float], candles: list | None = None) -> Signal:
    """Universal fallback: +1 up-move, -1 down-move, 0 flat. Never raises."""
    if not price_history or len(price_history) < 2:
        return 0.0, "insufficient history"
    last, prev = price_history[-1], price_history[-2]
    if last > prev:
        return 1.0, f"momentum up ({prev}->{last})"
    if last < prev:
        return -1.0, f"momentum down ({prev}->{last})"
    return 0.0, "flat"


BUILTINS: dict[str, Callable[..., Signal]] = {
    "simple_momentum": simple_momentum,
}
