# Local Smoke Test — alpha paper-trade flow

Goal: validate the agent spawn + trading + callbacks flow **locally via docker-compose**, bypassing hub/Morph, before burning another Morph snapshot rebuild cycle. Hits user-server directly (protected by `X-Hub-Secret` header).

**Auth note**: user-server `/agents/*`, `/hub/logs/*`, `/hub/trades/*`, `/hub/secrets/refresh` all check `X-Hub-Secret` against `settings.HUB_SECRET` (not `INTERNAL_SECRET`). See `user-server/user_server/security.py:hub_guard`. The two secrets serve different paths — `INTERNAL_SECRET` is for agent→user-server push calls via `internal_guard`.

Target: prove
- user-server spawns a real `app/` container
- engine starts ticking
- `hub_callback` pushes reach user-server
- `log_entries` + `trades` rows get written to user-server's DB
- `/hub/trades/{id}` and `/hub/logs/{id}` return those rows

## Environment

Repo: `/home/sounak/programming/silonelabs/hashkey`
Stack: `docker-compose.dev.yml` (services: hub-db, hub, user-server-db, user-server, all on `artic-dev` network)
User-server listens on host port **9100**. X-Hub-Secret = `INTERNAL_SECRET` from `.env.dev`.

## Prompt to Sonnet

> Repo: `/home/sounak/programming/silonelabs/hashkey`. Run an end-to-end local smoke test of the Artic paper-trade flow, bypassing hub and Morph. Work step by step; stop and report if anything fails.
>
> **Known state**: `.env.dev` exists with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `INTERNAL_SECRET`, `KEK`. The value of `TWELVE_DATA_API_KEY` in `.env.dev` is empty; ask the user to paste their Twelve Data key if the engine errors on missing market data, otherwise proceed without it (engine will still tick and we only need connectivity proof).
>
> ### Step 1 — build the local agent image
>
> ```bash
> docker build -t artic-app:dev -f app/Dockerfile .
> ```
> `user-server/Dockerfile` builds via docker-compose. Confirm image exists: `docker images | grep artic-app`.
>
> ### Step 2 — bring up the stack
>
> ```bash
> docker compose -f docker-compose.dev.yml --env-file .env.dev up -d --build
> ```
> Wait 10s. Confirm: `docker compose -f docker-compose.dev.yml ps` shows hub, user-server, hub-db, user-server-db all healthy/Up.
>
> ### Step 3 — run DB migrations (user-server)
>
> ```bash
> docker compose -f docker-compose.dev.yml --env-file .env.dev exec user-server alembic upgrade head
> ```
> If this path is wrong, locate the alembic config in `user-server/alembic.ini` and run with `-c` flag. If there's no alembic setup, check if user-server auto-creates tables on startup (look at `user-server/user_server/server.py` lifespan/startup) — may already be done.
>
> ### Step 4 — populate `secrets_cache` via `/hub/secrets/refresh`
>
> The agent container needs `GEMINI_API_KEY` and `TWELVE_DATA_API_KEY`. Normally hub pushes these on VM wake — locally we fake it:
>
> ```bash
> SECRET=$(grep ^HUB_SECRET= .env.dev | cut -d= -f2-)  # X-Hub-Secret header is validated against HUB_SECRET, not INTERNAL_SECRET
> TWELVE=$(grep ^TWELVE_DATA_API_KEY= .env.dev | cut -d= -f2-)
> # Ask user for their real Gemini key (GEMINI_API_KEY) — paste directly or from .env.dev if present
> GEMINI="<ASK USER>"
>
> curl -sf -X POST http://localhost:9100/hub/secrets/refresh \
>   -H "X-Hub-Secret: $SECRET" \
>   -H "Content-Type: application/json" \
>   -d "{\"secrets\": {\"GEMINI_API_KEY\": \"$GEMINI\", \"TWELVE_DATA_API_KEY\": \"$TWELVE\"}}"
> ```
> Expect HTTP 2xx. If the endpoint path differs, grep `hub/secrets/refresh` in `user-server/` to locate it.
>
> ### Step 5 — create an agent directly on user-server
>
> ```bash
> AGENT_JSON=$(curl -sf -X POST http://localhost:9100/agents \
>   -H "X-Hub-Secret: $SECRET" \
>   -H "Content-Type: application/json" \
>   -d '{
>     "name":"smoke",
>     "symbol":"BTCUSDT",
>     "llm_provider":"gemini",
>     "llm_model":"gemini-2.5-pro",
>     "strategy_pool":["momentum"],
>     "risk_params":{"amount_usdt":100,"leverage":1,"poll_seconds":5,"supervisor_interval":60}
>   }')
> echo "$AGENT_JSON"
> AGENT_ID=$(echo "$AGENT_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
> echo "agent: $AGENT_ID"
> ```
>
> ### Step 6 — start the agent
>
> ```bash
> curl -sf -X POST "http://localhost:9100/agents/$AGENT_ID/start" -H "X-Hub-Secret: $SECRET" | python3 -m json.tool
> ```
> This will: spawn `artic-agent-<id>` container on `artic-dev` network, wait for health, POST `/start` to the engine. Expect status=`alive`.
>
> ### Step 7 — watch the agent container logs
>
> ```bash
> sleep 5
> docker logs "artic-agent-$AGENT_ID" --tail=60
> ```
> Expect to see:
> - uvicorn Started server
> - `POST /start HTTP/1.1" 200 OK`
> - `[TICK] BTCUSDT price=$...` lines (or errors if TWELVE_DATA_API_KEY is empty — that's fine for a connectivity check, not fine for PnL)
> - **No** `log flush failed` or `Name or service not known` errors — the agent should reach user-server via the `artic-dev` Docker network DNS name `user-server`.
>
> ### Step 8 — verify callbacks landed in user-server DB
>
> ```bash
> docker compose -f docker-compose.dev.yml exec user-server-db psql -U artic -d artic -c "SELECT COUNT(*) FROM log_entries WHERE agent_id='$AGENT_ID';"
> docker compose -f docker-compose.dev.yml exec user-server-db psql -U artic -d artic -c "SELECT status, unrealized_pnl_usdt, current_strategy FROM agents WHERE id='$AGENT_ID';"
> docker compose -f docker-compose.dev.yml exec user-server-db psql -U artic -d artic -c "SELECT COUNT(*) FROM trades WHERE agent_id='$AGENT_ID';"
> ```
> Expect `log_entries` count > 0 within 30s. `agents.status` = 'alive'. `current_strategy` may still be null if LLM planner hasn't kicked in yet. Trades may be 0 if market signal is weak — OK.
>
> ### Step 9 — verify the read paths work (what the dashboard uses)
>
> ```bash
> curl -sf "http://localhost:9100/hub/logs/$AGENT_ID?limit=5" -H "X-Hub-Secret: $SECRET" | python3 -m json.tool
> curl -sf "http://localhost:9100/hub/trades/$AGENT_ID?limit=5" -H "X-Hub-Secret: $SECRET" | python3 -m json.tool
> curl -sf "http://localhost:9100/agents/$AGENT_ID" -H "X-Hub-Secret: $SECRET" | python3 -m json.tool
> ```
> All should 200. `logs` should have entries. `trades` may be empty.
>
> ### Step 10 — cleanup
>
> ```bash
> curl -sf -X POST "http://localhost:9100/agents/$AGENT_ID/stop" -H "X-Hub-Secret: $SECRET" | python3 -m json.tool
> docker ps -a --filter name=artic-agent --format '{{.Names}}' | xargs -r docker rm -f
> ```
>
> ### What to report back
>
> - Which steps passed
> - Full `docker logs artic-agent-<id>` for step 7
> - The DB counts from step 8
> - The JSON responses from step 9 (truncate logs to first 2 entries)
> - Any error encountered and what you did about it
>
> **Do not rebuild the Morph golden snapshot.** This test is purely local — it validates code correctness, network/callback wiring, and DB writes. If it passes, we then rebuild the Morph snapshot with confidence.

---

## Expected outcomes

| Check | Pass criteria |
|---|---|
| Agent container spawns | `docker ps` shows `artic-agent-<id>` |
| Engine starts | `POST /start` returns 200 in container logs |
| Callbacks reach user-server | No `log flush failed` errors |
| Logs persisted | `SELECT COUNT(*) FROM log_entries` > 0 |
| Status persisted | `agents.status='alive'`, `unrealized_pnl_usdt` updates over time |
| Dashboard endpoints return data | `/hub/logs/{id}` has rows |

## Known gotchas

- If `USER_SERVER_INTERNAL_URL` env override in compose says `http://user-server:8000`, agent container can resolve that via `artic-dev` Docker DNS — good. If it's been changed to `host.docker.internal`, revert for local testing (or override at runtime).
- `AGENT_IMAGE` in compose is `artic-app:dev` — must match what Step 1 builds.
- If user-server's alembic has no `versions/` dir, tables may be created via `Base.metadata.create_all` at startup — check `user-server/user_server/server.py` lifespan.
- If `/hub/secrets/refresh` returns 401, the `X-Hub-Secret` header doesn't match `INTERNAL_SECRET`. Verify with `docker compose exec user-server printenv INTERNAL_SECRET`.
