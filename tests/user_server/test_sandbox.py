"""Sandbox coverage: violations must fall back, not crash the server.

These tests don't need Postgres — pure runner unit tests.
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@x:5432/x")

from user_server.strategies.runner import run  # noqa: E402


PLAN = {"lookback": 5}
HIST = [100.0, 101.0, 102.0]


def test_builtin_simple_momentum():
    r = run("simple_momentum", None, PLAN, HIST)
    assert not r.fallback
    assert r.signal[0] == 1.0


def test_unknown_builtin_no_source_falls_back():
    r = run("nonexistent", None, PLAN, HIST)
    assert r.fallback
    assert "no source" in (r.error or "")


def test_authored_good_code():
    src = """
def compute(plan, price_history, candles):
    return (0.5, 'ok')
"""
    r = run("my_strat", src, PLAN, HIST)
    assert not r.fallback, r.error
    assert r.signal == (0.5, "ok")


def test_authored_infinite_loop_timeout():
    src = """
def compute(plan, price_history, candles):
    while True:
        pass
"""
    r = run("loopy", src, PLAN, HIST, timeout_ms=500)
    assert r.fallback
    assert "exceeded" in (r.error or "")


def test_authored_import_os_blocked():
    src = """
import os
def compute(plan, price_history, candles):
    return (0.0, os.getcwd())
"""
    r = run("bad_import", src, PLAN, HIST)
    assert r.fallback
    assert r.error is not None


def test_authored_missing_compute():
    src = """
x = 1
"""
    r = run("no_compute", src, PLAN, HIST)
    assert r.fallback
    assert "compute" in (r.error or "")


def test_authored_bad_return_shape():
    src = """
def compute(plan, price_history, candles):
    return 42
"""
    r = run("bad_return", src, PLAN, HIST)
    assert r.fallback
    assert "bad shape" in (r.error or "")


def test_authored_open_file_blocked():
    src = """
def compute(plan, price_history, candles):
    open('/etc/passwd')
    return (0.0, '')
"""
    r = run("open_file", src, PLAN, HIST)
    assert r.fallback
