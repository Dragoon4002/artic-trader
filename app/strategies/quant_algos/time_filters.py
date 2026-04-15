"""
Time / session filters (return 1 = allow trade, 0 = block).
"""
from datetime import datetime, time
from typing import Tuple, Optional


def session_filter(
    utc_hour_start: int = 13, utc_hour_end: int = 21, **_
) -> Tuple[float, str]:
    """Allow trading only between utc_hour_start and utc_hour_end. Return 1 = allow, 0 = block."""
    now = datetime.utcnow()
    h = now.hour + now.minute / 60
    if utc_hour_start <= utc_hour_end:
        allow = utc_hour_start <= h < utc_hour_end
    else:
        allow = h >= utc_hour_start or h < utc_hour_end
    sig = 1.0 if allow else 0.0
    return sig, f"session UTC {h:.1f}h in [{utc_hour_start},{utc_hour_end})={allow}"


def day_of_week_filter(
    allow_days: Optional[tuple] = None, **_
) -> Tuple[float, str]:
    """Allow only certain weekdays. 0=Mon, 6=Sun. Default (0,1,2,3,4) = weekdays."""
    if allow_days is None:
        allow_days = (0, 1, 2, 3, 4)
    now = datetime.utcnow()
    wd = now.weekday()
    allow = wd in allow_days
    sig = 1.0 if allow else 0.0
    return sig, f"weekday={wd} allow={allow}"
