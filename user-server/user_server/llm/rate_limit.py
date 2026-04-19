"""Token-bucket rate limiter. 60/min across all agents on this VM.

One user per VM = per-user == per-process. Agent-level counters are
lightweight observability and don't gate — A4 scope stays minimal.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from shared.errors import RateLimited


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = float(capacity)
        self.last = time.monotonic()
        self._lock = Lock()

    def take(self, cost: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_per_sec)
            self.last = now
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False


_bucket = TokenBucket(capacity=60, refill_per_sec=60 / 60)  # 60/min
_agent_counts: dict[str, int] = defaultdict(int)


def check_and_count(agent_id: str | None) -> None:
    if not _bucket.take():
        raise RateLimited("LLM proxy: 60/min per VM exceeded")
    if agent_id:
        _agent_counts[agent_id] += 1


def counts() -> dict[str, int]:
    return dict(_agent_counts)


def reset() -> None:
    """Test hook."""
    global _bucket
    _bucket = TokenBucket(capacity=60, refill_per_sec=60 / 60)
    _agent_counts.clear()
