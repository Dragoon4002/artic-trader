# Alpha Fix Plan — end-to-end paper-trade + PnL

Goal: user logs in → creates agent → hub wakes VM from golden snapshot → user-server spawns agent container → container runs paper trading → dashboard shows live PnL + trades + logs.

## Break Points (confirmed)

### B1. Agent `/start` never called after spawn *(CRITICAL)*
**File**: `user-server/user_server/agents/service.py:78-92` (`start()`).
`spawner.spawn()` launches the Docker container, but no HTTP call is made to `POST http://artic-agent-<id>:8000/start` with the StartRequest body. Engine boots dormant (`engine.running=False`), so no market polls, no trades, no log flushes.

### B2. `USER_SERVER_URL`/`HUB_URL` hard-coded to `localhost` *(CRITICAL)*
**File**: `user-server/user_server/agents/spawner.py:131-133` (`_self_url`).
Returns `"http://localhost:8000"`. Inside the agent container, localhost = itself, not user-server. On the agent Docker network, user-server is reachable at its container name (typically `user-server:8000` or via `AGENT_NETWORK` DNS). Result: every `hub_callback.report_*` call silently fails, so no status, no trades, no logs reach user-server.

### B3. Dashboard reads trades from wrong table *(CRITICAL)*
**Write path**: `app/hub_callback.py:62` → user-server `push_router.py:81` → `Trade` SQLA table.
**Read path**: dashboard `clients/web/lib/api.ts:176` calls `GET /api/v1/u/hub/indexer/since` → `user-server/indexer/query.py` → `IndexerTx` table.
Nothing writes `Trade` rows into `IndexerTx`. Dashboard will always show empty trades list → empty PnL chart.

**Decision: Option (b)** — new endpoint `GET /hub/trades/{agent_id}` on user-server reading the `Trade` table, auto-proxied via `/api/v1/u/*`, web `listTrades` points at it. Chosen because `Trade`/`Agent` carry no `user_id` (scoping is implicit per-user-VM); option (a) would require synthesizing user_id.

### B4. `unrealised_pnl` field dropped by web client *(MEDIUM)*
**File**: `clients/web/lib/api.ts:43-88`.
`BackendAgent` type is missing `unrealized_pnl_usdt` and `current_strategy`; `toClientAgent` hard-codes `unrealised_pnl: null`. Even if push_status works, dashboard never shows it. AgentOut (user-server `agents/router.py:28-37`) already returns both fields.

### B5. Default strategy_pool is empty *(MEDIUM)*
**File**: `clients/web/lib/api.ts:112` packs `strategy_pool: [body.strategy]` — OK if UI picks one. But engine's LLM planner with `STRATEGY_POOL=[]` can deadlock or pick nothing. Verify `clients/web/app/app/agents/new/page.tsx` always sets `strategy`.

### B6. `/start` payload not built from agent row *(CRITICAL — coupled to B1)*
Required by `app/main.py:198-228` StartRequest: `symbol, amount_usdt, leverage, poll_seconds, tp_pct, sl_pct, risk_profile, primary_timeframe, supervisor_interval_seconds, live_mode=false, tp_sl_mode, llm_provider, indicators`. Must be derived from `agent.symbol` + `agent.risk_params` JSON. Missing fields → use defaults (`live_mode=False`, `tp_sl_mode="fixed"`, `risk_profile="moderate"`, `primary_timeframe="15m"`).

### B7. Container hostname resolution
Spawner names containers `artic-agent-<uuid>` (`spawner.py:48-49`). If user-server is on the same Docker network (`AGENT_NETWORK` / `artic-dev`), DNS will resolve. Verify `docker-compose.dev.yml` puts user-server on the same network as `AGENT_NETWORK` value. If not, start URL should use container IP (fetch via `container.reload(); container.attrs['NetworkSettings']...`).

### B8. Health-wait before POST /start
Container boot + uvicorn startup takes ~2-5s. Poll `GET http://artic-agent-<id>:8000/health` with short timeout until ok or 15s deadline, THEN POST /start. Otherwise first POST may hit connection-refused.

## Verification checklist (must pass before "done")
- [ ] `docker logs artic-agent-<id>` shows "Started server" AND "[Engine] running loop" style tick logs
- [ ] `psql` shows rows in `log_entries` for the agent within 30s
- [ ] `psql` shows rows in `trades` (or `indexer_tx` with kind='trades' per fix B3)
- [ ] Dashboard `/app/agents/<id>` shows non-zero trade count + populated PnL chart
- [ ] Dashboard shows `unrealised_pnl` value (non-null) when position open

---

# Sonnet-ready prompts

Each prompt is self-contained; hand to Sonnet one at a time. Run in order.

---

## PROMPT 1 — Wire user-server→agent /start call

> Repo: `/home/sounak/programming/silonelabs/hashkey`.
>
> Fix `user-server/user_server/agents/service.py:start()`. Currently it spawns the container but never tells the app engine to begin trading. After `spawner.spawn(...)`, do:
>
> 1. Import `httpx` at top of file.
> 2. After line 88 (registry.put), resolve agent base URL with a DNS-first, IP-fallback strategy:
>    - First try hostname: `agent_base = f"http://{spawner.container_name(agent.id)}:8000"` and attempt `GET /health` once (1s timeout).
>    - If that fails (connection error / DNS error), fetch the container's IP on the agent network:
>      ```python
>      await asyncio.to_thread(container.reload)
>      nets = container.attrs["NetworkSettings"]["Networks"]
>      net = nets.get(settings.AGENT_NETWORK) or next(iter(nets.values()))
>      ip = net["IPAddress"]
>      agent_base = f"http://{ip}:8000"
>      ```
>    - Add `spawner` helper `inspect_ip(container, network: str) -> str` if it keeps service.py clean; otherwise inline is fine.
> 3. Poll `GET {agent_base}/health` every 0.5s up to 15s, break when 200 OK. If timeout, raise `shared.errors.Validation("agent container failed to become healthy")` after best-effort `spawner.stop(container.id)` + `registry.remove`.
> 4. Build StartRequest payload from `agent`:
>    ```python
>    rp = agent.risk_params or {}
>    payload = {
>        "symbol": agent.symbol,
>        "amount_usdt": rp.get("amount_usdt", 100),
>        "leverage": rp.get("leverage", 1),
>        "poll_seconds": rp.get("poll_seconds", 5),
>        "tp_pct": rp.get("tp_pct"),
>        "sl_pct": rp.get("sl_pct"),
>        "risk_profile": rp.get("risk_profile", "moderate"),
>        "primary_timeframe": rp.get("primary_timeframe", "15m"),
>        "live_mode": False,
>        "tp_sl_mode": rp.get("tp_sl_mode", "fixed"),
>        "supervisor_interval_seconds": rp.get("supervisor_interval", 60),
>        "llm_provider": agent.llm_provider,
>    }
>    ```
> 5. POST `{agent_base}/start` with json=payload, 10s timeout. On non-2xx, log warning but still mark agent alive (engine may self-recover on retry).
> 6. Set `agent.status = "alive"` only after the POST returns.
>
> Use one module-level `httpx.AsyncClient` (lazily initialized) or a short-lived client per call — either fine. Do NOT block the event loop — everything async.
>
> Don't touch any other file. Don't add comments explaining the new code. Run `ruff check` on the file when done.

---

## PROMPT 2 — Fix user-server URL visible to agents

> Repo: `/home/sounak/programming/silonelabs/hashkey`.
>
> In `user-server/user_server/agents/spawner.py:_self_url()`, `http://localhost:8000` is wrong — agents on the Docker network can't reach user-server that way. Replace with an env-configurable URL.
>
> 1. In `user-server/user_server/config.py`, add `USER_SERVER_INTERNAL_URL: str = "http://user-server:8000"` to Settings. This is the URL agent containers use to reach user-server on the shared Docker network.
> 2. In `spawner.py`, change `_self_url` location: delete it from `service.py` (or update there too) — actually `_self_url()` lives in `service.py:131`. Update `service.py` to use `settings.USER_SERVER_INTERNAL_URL` instead of the hard-coded localhost string. Remove the `_self_url()` helper if it becomes trivial.
> 3. Verify `docker-compose.dev.yml` sets `USER_SERVER_INTERNAL_URL` env for user-server (or that the default matches the service name there).
> 4. Confirm user-server and the agent network share `AGENT_NETWORK`. If user-server's docker-compose service is not attached to that network, add it.
>
> Don't add comments. Run `ruff check`.

---

## PROMPT 3 — Surface trades to dashboard via new user-server endpoint

> Repo: `/home/sounak/programming/silonelabs/hashkey`. Problem: web dashboard reads trades from `/api/v1/u/hub/indexer/since` → `IndexerTx` table, but `push_router.push_trade` writes to the `Trade` table. Dashboard always empty.
>
> Solution: add a new read endpoint on user-server and point the web client at it.
>
> 1. Create `user-server/user_server/trades/__init__.py` (empty) and `user-server/user_server/trades/query.py`:
>    - `APIRouter(prefix="/hub/trades", dependencies=[Depends(hub_guard)])`
>    - Model `TradeRow` with fields matching the web client's expected `Trade` shape (see `clients/web/lib/api.ts:184-198`): `id, agent_id, side, entry_price (float), exit_price (float|None), size_usdt (float), leverage, pnl_usdt (float|None), strategy, open_at, close_at, close_reason`.
>    - Endpoint `GET /{agent_id}?limit=500` returns `{"rows": [...]}` ordered by `open_at DESC`.
> 2. Register the router in `user-server/user_server/server.py` (find where `indexer/query` router is registered, add this one next to it).
> 3. Update `clients/web/lib/api.ts:listTrades`:
>    - If `agentId` provided, hit `/api/v1/u/hub/trades/${agentId}` and map rows directly.
>    - If no `agentId`, keep the indexer fallback OR (preferred) loop over `listAgents()` and concat — simpler: add a new endpoint `/hub/trades?limit=500` returning all trades, or iterate agents client-side. For now, make `listTrades(agentId)` require agentId and update callers that pass undefined in `clients/web/app/app/agents/page.tsx:35`.
>    - Update the row → `Trade` mapper to read from new shape.
>
> Don't add comments. Keep `Trade` type in `clients/web/lib/schemas.ts` unchanged — map into it.

---

## PROMPT 4 — Expose unrealised_pnl + active_strategy to web client

> Repo: `/home/sounak/programming/silonelabs/hashkey`. The web `BackendAgent` interface in `clients/web/lib/api.ts:43-63` is missing `unrealized_pnl_usdt` and `current_strategy`. The user-server `AgentOut` (`user-server/user_server/agents/router.py:28`) already returns them.
>
> 1. Add `unrealized_pnl_usdt: number | null` and `current_strategy: string | null` to `BackendAgent`.
> 2. In `toClientAgent`, set `unrealised_pnl: b.unrealized_pnl_usdt ?? null` and `strategy: b.current_strategy ?? b.strategy_pool[0] ?? "unknown"`.
>
> That's it. Don't add comments.

---

## PROMPT 5 — Verify paper-trade loop actually emits trades

> Repo: `/home/sounak/programming/silonelabs/hashkey`.
>
> The engine loop is at `app/engine.py`. I need to verify trades are actually emitted. Trace the code path:
>
> 1. `app/engine.py` — find the tick loop (look for `while self.running` or similar). Confirm it calls some version of `_execute_action` that opens/closes positions through `app/executor/paper.py`.
> 2. Confirm on trade open AND close, `hub_callback.report_trade(trade_dict)` is called with fields matching `HubCallback.report_trade` (`agent_id, side, entry_price, exit_price, size_usdt, leverage, pnl, strategy, close_reason`).
> 3. Confirm `hub_callback.flush_logs(agent_id)` is called periodically (every N ticks is fine).
> 4. Confirm `hub_callback.report_status(agent_id, status)` is called each tick with `{last_price, position_size_usdt, unrealized_pnl_usdt, active_strategy}`.
> 5. If any of these is missing or mis-shaped, fix it in engine.py. Don't rewrite the loop — just patch call sites.
>
> After editing, report what you changed and why. If everything is already wired correctly, say so and move on.

---

## PROMPT 6 — End-to-end smoke test

> Repo: `/home/sounak/programming/silonelabs/hashkey`. All fixes applied. Run an end-to-end test.
>
> 1. `docker compose -f docker-compose.dev.yml up --build -d`
> 2. Wait 30s. `docker compose logs hub user-server --tail=50` — confirm healthy.
> 3. Using a test user JWT (or create one via `/auth/*` if easy), POST to hub `/api/v1/u/agents` with a minimal body: `{"name":"smoke","symbol":"BTC/USD","llm_provider":"anthropic","llm_model":"claude-sonnet-4-5","strategy_pool":["sma_cross"],"risk_params":{"amount_usdt":100,"leverage":1,"poll_seconds":5}}`.
> 4. POST `/api/v1/u/agents/<id>/start`.
> 5. `docker ps | grep artic-agent` — confirm container running.
> 6. `docker logs artic-agent-<id> --tail=50` — confirm engine ticking.
> 7. Wait 60s. `psql` into hub DB (check compose for creds): `SELECT COUNT(*) FROM log_entries WHERE agent_id=...; SELECT COUNT(*) FROM trades WHERE agent_id=...;`. Both > 0.
> 8. Open dashboard `http://localhost:3000/app/agents/<id>` — confirm trades list + PnL chart populated.
>
> If any step fails, capture logs + state and report before trying to fix.

---

## Decisions (locked)

- Golden snapshot exists on Morph; user-server+DB baked in. Wake flow via real MorphProvider.
- VM_PROVIDER=morph only. No local mock path; dev = Morph.
- `INTERNAL_SECRET` shared by hub + user-server + agent env. Set once in `.env.dev`.
- **B3 fix = Option (b)**: new `GET /hub/trades/{agent_id}` endpoint on user-server. Reason: `Trade` has no `user_id` (only `agent_id` FK); `Agent` also has no `user_id`. Scoping is implicit per-user-VM-DB. Dual-writing to `IndexerTx` would need synthesized user_id from request context — extra work. New endpoint is strictly simpler.
- Smoke test (Prompt 6) must run against Morph, not local-only docker. Skip local-only fallback steps.
