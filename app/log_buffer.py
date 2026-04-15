"""
In-memory log buffer for AI engine output. Used to stream live logs to frontend.
"""
from datetime import datetime
from typing import List, Literal
from collections import deque

LogLevel = Literal["init", "llm", "start", "tick", "action", "sl_tp", "stop", "error", "warn", "supervisor"]

_MAX_LOGS = 2000
_buffer: deque = deque(maxlen=_MAX_LOGS)


def emit(level: LogLevel, message: str) -> None:
    """Append a log line to buffer, print to stdout, and buffer for hub push."""
    ts = datetime.utcnow().isoformat() + "Z"
    entry = {"ts": ts, "level": level, "message": message}
    _buffer.append(entry)
    print(message)
    # Buffer for hub callback (fire-and-forget, no-op if hub not configured)
    try:
        from . import hub_callback
        hub_callback.buffer_log(level, message)
    except Exception:
        pass


def clear() -> None:
    """Clear the log buffer (e.g. on new session start)."""
    _buffer.clear()


def get_logs(limit: int = 500) -> List[dict]:
    """Return last `limit` log entries, newest last."""
    items = list(_buffer)
    if limit and len(items) > limit:
        items = items[-limit:]
    return items


def get_logs_response(running: bool) -> dict:
    """Response shape for GET /logs."""
    return {
        "logs": get_logs(),
        "running": running,
    }
