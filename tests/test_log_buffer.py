from app import log_buffer


def setup_function():
    log_buffer.clear()


def test_get_logs_returns_only_requested_tail():
    for index in range(10):
        log_buffer.emit("tick", f"tick-{index}")

    logs = log_buffer.get_logs(limit=3)

    assert [entry["message"] for entry in logs] == ["tick-7", "tick-8", "tick-9"]


def test_get_logs_keeps_existing_unlimited_behavior():
    for index in range(3):
        log_buffer.emit("tick", f"tick-{index}")

    logs = log_buffer.get_logs(limit=0)

    assert [entry["message"] for entry in logs] == ["tick-0", "tick-1", "tick-2"]
