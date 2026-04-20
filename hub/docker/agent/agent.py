"""V0 agent stub.

No trading. No LLM. No market data. Just proves container ran:
- Dumps all env vars at startup (visible via `docker logs agent-<id>`)
- Serves GET /health on :8080
- Posts heartbeat to USER_SERVER_URL/internal/v1/agents/{id}/status every 10s
  with X-Internal-Secret header.

Replaces the full tick loop once trading lands.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

AGENT_ID = os.environ.get("HUB_AGENT_ID", "unknown")
SYMBOL = os.environ.get("SYMBOL", "BTCUSDT")
USER_SERVER_URL = os.environ.get("USER_SERVER_URL", "http://host.docker.internal:8000")
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "")
HEARTBEAT_SECONDS = int(os.environ.get("HEARTBEAT_SECONDS", "10"))


def log(msg: str) -> None:
    sys.stdout.write(f"[agent {AGENT_ID[:8]}] {msg}\n")
    sys.stdout.flush()


def dump_env() -> None:
    log("=== agent boot ===")
    for key in sorted(os.environ):
        value = os.environ[key]
        if "SECRET" in key or "KEY" in key or "TOKEN" in key:
            value = f"<redacted {len(value)}c>"
        log(f"  {key}={value}")
    log("=== end env ===")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path in ("/health", "/healthz"):
            body = json.dumps({"ok": True, "agent_id": AGENT_ID, "symbol": SYMBOL}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_args: object) -> None:  # silence default access log
        return


def run_health_server() -> None:
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log("health server listening on :8080")
    server.serve_forever()


def heartbeat_loop() -> None:
    url = f"{USER_SERVER_URL.rstrip('/')}/agents/{AGENT_ID}/status"
    headers = {"X-Internal-Secret": INTERNAL_SECRET, "Content-Type": "application/json"}
    tick = 0
    # Body matches user_server.agents.push_router.StatusPush. Numbers are stubs
    # until the trading loop lands; heartbeat just proves the container's alive.
    while True:
        payload = {
            "price": 0.0,
            "position_size_usdt": 0.0,
            "unrealized_pnl_usdt": 0.0,
        }
        try:
            r = httpx.post(url, json=payload, headers=headers, timeout=5)
            log(f"heartbeat #{tick} → {r.status_code}")
        except Exception as e:  # noqa: BLE001 — swallow, keep looping
            log(f"heartbeat #{tick} failed: {e}")
        tick += 1
        time.sleep(HEARTBEAT_SECONDS)


def main() -> None:
    signal.signal(signal.SIGTERM, lambda *_: (log("SIGTERM — exiting"), sys.exit(0)))
    dump_env()
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    heartbeat_loop()


if __name__ == "__main__":
    main()
