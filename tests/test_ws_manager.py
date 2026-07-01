import asyncio
import time

from hub.ws import manager


class FakeWebSocket:
    def __init__(self, *, delay: float = 0.0, fail: bool = False):
        self.delay = delay
        self.fail = fail
        self.messages: list[str] = []

    async def send_text(self, payload: str) -> None:
        await asyncio.sleep(self.delay)
        if self.fail:
            raise RuntimeError("closed")
        self.messages.append(payload)


def clear_subscribers() -> None:
    manager._subscribers.clear()
    manager._price_subscribers.clear()


def test_agent_broadcast_sends_to_slow_subscribers_concurrently():
    async def run() -> None:
        clear_subscribers()
        sockets = [FakeWebSocket(delay=0.03) for _ in range(8)]
        for ws in sockets:
            await manager.subscribe("agent-1", ws)

        start = time.perf_counter()
        await manager.broadcast("agent-1", "status", {"ok": True})
        elapsed = time.perf_counter() - start

        assert elapsed < 0.12
        assert all(len(ws.messages) == 1 for ws in sockets)
        clear_subscribers()

    asyncio.run(run())


def test_price_broadcast_sends_to_slow_subscribers_concurrently_and_removes_dead():
    async def run() -> None:
        clear_subscribers()
        live = [FakeWebSocket(delay=0.03) for _ in range(6)]
        dead = FakeWebSocket(delay=0.03, fail=True)
        for ws in [*live, dead]:
            await manager.subscribe_prices(ws)

        start = time.perf_counter()
        await manager.broadcast_prices({"BTCUSDT": {"price": 100.0}})
        elapsed = time.perf_counter() - start

        assert elapsed < 0.12
        assert all(len(ws.messages) == 1 for ws in live)
        assert dead not in manager._price_subscribers
        clear_subscribers()

    asyncio.run(run())