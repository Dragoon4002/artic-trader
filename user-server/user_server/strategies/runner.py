"""RestrictedPython executor. Compile-then-exec with static safety + wall-clock
timeout via SIGALRM. Any violation falls back to `simple_momentum` and emits
a log entry. Memory-cap via RLIMIT_AS is deferred — see user-vm.md §Strategy
runner (subprocess isolation is zone work post-alpha).
"""
from __future__ import annotations

import math
import signal
import statistics
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    safer_getattr,
)

from .builtins import BUILTINS, Signal, simple_momentum


class SandboxViolation(Exception):
    """Raised when the user strategy blows a sandbox guarantee (time, import, etc.)."""


class SandboxTimeout(SandboxViolation):
    pass


@dataclass
class RunResult:
    signal: Signal
    strategy_name: str  # name that actually produced the signal (may be the fallback)
    fallback: bool
    error: str | None = None


@contextmanager
def _timeout(ms: int):
    """SIGALRM-based; only works on the main thread of the main interpreter."""

    def _handler(_signum, _frame):
        raise SandboxTimeout(f"strategy exceeded {ms}ms")

    sec = max(1, round(ms / 1000))
    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(sec)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def _safe_globals() -> dict[str, Any]:
    return {
        "__builtins__": {**safe_builtins, "math": math, "statistics": statistics},
        "_getattr_": safer_getattr,
        "_getiter_": iter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
    }


def run(
    strat_name: str,
    strat_source: str | None,
    plan: dict,
    price_history: list[float],
    candles: list | None = None,
    timeout_ms: int = 500,
) -> RunResult:
    """Execute a strategy. Name matches a builtin or `strat_source` is compiled/executed.

    Guarantees: no unhandled exception escapes; on any sandbox violation the
    fallback runs and a human-readable error is set.
    """
    if strat_name in BUILTINS and strat_source is None:
        try:
            sig = BUILTINS[strat_name](plan, price_history, candles)
            return RunResult(signal=sig, strategy_name=strat_name, fallback=False)
        except Exception as exc:  # noqa: BLE001
            return _fallback(plan, price_history, candles, error=f"builtin raised: {exc}")

    if not strat_source:
        return _fallback(plan, price_history, candles, error=f"no source for {strat_name!r}")

    try:
        code = compile_restricted(strat_source, filename="<strategy>", mode="exec")
    except SyntaxError as exc:
        return _fallback(plan, price_history, candles, error=f"compile: {exc}")

    globs = _safe_globals()
    locs: dict[str, Any] = {}
    try:
        with _timeout(timeout_ms):
            exec(code, globs, locs)  # noqa: S102 — sandboxed
            compute = locs.get("compute") or globs.get("compute")
            if not callable(compute):
                raise SandboxViolation("strategy missing callable `compute(plan, price_history, candles)`")
            sig = compute(plan, price_history, candles)
        if not (
            isinstance(sig, tuple) and len(sig) == 2 and isinstance(sig[0], (int, float)) and isinstance(sig[1], str)
        ):
            raise SandboxViolation(f"strategy returned bad shape: {type(sig).__name__}")
        return RunResult(signal=(float(sig[0]), sig[1]), strategy_name=strat_name, fallback=False)
    except SandboxTimeout as exc:
        return _fallback(plan, price_history, candles, error=str(exc))
    except SandboxViolation as exc:
        return _fallback(plan, price_history, candles, error=f"violation: {exc}")
    except Exception as exc:  # noqa: BLE001 — catch-all; sandbox must never crash user-server
        return _fallback(plan, price_history, candles, error=f"error: {type(exc).__name__}: {exc}")


def _fallback(plan: dict, price_history: list[float], candles: list | None, *, error: str) -> RunResult:
    sig = simple_momentum(plan, price_history, candles)
    return RunResult(signal=sig, strategy_name="simple_momentum", fallback=True, error=error)
