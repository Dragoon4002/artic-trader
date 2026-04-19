"""Gas-bump retry helper. 3 attempts, +20% gas each, 120s total budget."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass
class RetryOutcome:
    attempts: int
    gas_prices: list[int]
    tx_hash: str | None
    receipt: dict | None
    error: str | None = None


async def with_gas_bump(
    send: Callable[[int], Awaitable[str]],
    wait_receipt: Callable[[str], Awaitable[dict | None]],
    *,
    initial_gas_price: int,
    bump_pct: float = 0.20,
    max_attempts: int = 3,
    total_budget_sec: float = 120.0,
) -> RetryOutcome:
    gas = initial_gas_price
    attempts = 0
    gas_prices: list[int] = []
    start = time.monotonic()
    last_err: str | None = None

    while attempts < max_attempts and (time.monotonic() - start) < total_budget_sec:
        attempts += 1
        gas_prices.append(gas)
        try:
            tx_hash = await send(gas)
        except Exception as exc:  # noqa: BLE001
            last_err = f"send: {exc}"
            gas = int(gas * (1 + bump_pct))
            continue

        remaining = total_budget_sec - (time.monotonic() - start)
        try:
            receipt = await asyncio.wait_for(wait_receipt(tx_hash), timeout=max(1.0, remaining))
        except asyncio.TimeoutError:
            last_err = "receipt timeout"
            gas = int(gas * (1 + bump_pct))
            continue

        if receipt and receipt.get("status") in (1, "0x1"):
            return RetryOutcome(attempts=attempts, gas_prices=gas_prices, tx_hash=tx_hash, receipt=receipt)

        last_err = f"receipt status {receipt.get('status') if receipt else 'None'}"
        gas = int(gas * (1 + bump_pct))

    return RetryOutcome(
        attempts=attempts, gas_prices=gas_prices, tx_hash=None, receipt=None, error=last_err or "exhausted"
    )
