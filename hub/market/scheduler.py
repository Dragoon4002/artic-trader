"""APScheduler wiring for market cache refresh."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..config import settings
from . import cache


def register(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        cache.refresh_all_tracked,
        "interval",
        seconds=settings.CANDLE_STALENESS_SECONDS,
        id="candle_refresh",
        replace_existing=True,
    )
