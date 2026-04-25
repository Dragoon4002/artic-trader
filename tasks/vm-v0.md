# VM v0 — "Spawn-Only" Flow

Form submit → Morph VM boots → user-server up → agent container running. Nothing else.

## Scope locked

| Topic | Decision |
|---|---|
| Provision trigger | Lazy — on first `POST /u/agents` |
| Agent stub | env dump + heartbeat every 10s to user-server `/agents/{id}/heartbeat` + `/health` |
| Base image source | `hub/docker/agent/` — source lives in hub repo |
| Customized image | Not in v0 — env-var customization at `docker run` only |
| Registry | `ghcr.io/silonelabs/artic-agent:v0`, `ghcr.io/silonelabs/artic-user-server:v0` |
| Snapshot ladder | Base (Morph blank) → Golden (Postgres 14 + dockerd + 2 ghcr images pre-pulled) → **no per-user snapshot in v0** |
| Hub↔user-server auth | `X-Hub-Secret` shared header (defer JWT/mTLS) |
| Cold-wake | Not wired — VM stays warm, pay idle cost, stop manually between runs |
| Dashboard auth | Stub login (current `/api/auth/login` accepts any valid email+password w/ mock flag off — needs hub email/password endpoint OR keep mock until v1) |

## Image matrix

| Image | Source | Entry | Purpose |
|---|---|---|---|
| `artic-agent:v0` | `hub/docker/agent/Dockerfile` | `python agent.py` | Prints env, POST /heartbeat every 10s, serves /health |
| `artic-user-server:v0` | `user-server/Dockerfile` (exists) | `uvicorn user_server.server:app` | FastAPI + Docker SDK (socket-mounted); spawns agents |

## Commit slices (branch `feat/vm-v0`, new worktree)

### Commit 1 — agent stub image
- `hub/docker/agent/Dockerfile` — python:3.12-slim, pip install httpx
- `hub/docker/agent/agent.py` — reads `AGENT_ID`, `USER_SERVER_URL`, `INTERNAL_SECRET`, `SYMBOL`; starts `/health` on 8080; loops heartbeat 10s
- Local build: `docker build -t artic-agent:v0 hub/docker/agent/`

### Commit 2 — user-server: agents CRUD + docker spawn
- Migration `0002_agents.py`: `agents` table (id, name, symbol, status, container_id, created_at)
- `user_server/agents/router.py`: GET /agents, POST /agents, GET /agents/{id}, GET /agents/{id}/status, DELETE /agents/{id}, POST /agents/{id}/heartbeat
- `user_server/agents/docker_manager.py`: port allocator + `client.containers.run("artic-agent:v0", detach=True, environment={...}, network="host", name=f"agent-{id}")`
- Heartbeat: update `agents.last_heartbeat` timestamp; status flips to `alive` on first heartbeat
- Requirements: `docker` python sdk

### Commit 3 — hub Morph wrapper
- `pip install morphcloud` (add to `hub/requirements.txt`)
- `hub/vm/morph.py`: `MorphProvider` class — `start_instance(snapshot_id)`, `wake_on_http(instance_id)`, `exec(cmd)`, `exposeHttpService("user-server", 80)`, `stop(instance_id)`
- Uses `MORPH_API_KEY`, `MORPH_BASE_URL` from env

### Commit 4 — hub: user_vms table + provision flow
- Migration `0003_user_vms.py`: `user_vms` (user_id PK, provider_vm_id, endpoint, status, created_at, updated_at)
- `hub/vm/service.py`: `provision(user_id)` — start golden instance → wake-on-http → `docker run user-server` → healthz poll → exposeHttpService → persist row → return endpoint

### Commit 5 — hub: /u/agents proxy
- `hub/u_proxy/router.py`: any `/api/v1/u/agents*` request
  - lookup `user_vms`; if none → `vm.service.provision(user_id)`
  - `httpx.request(method, f"{endpoint}{path}", headers={"X-Hub-Secret": ...}, json=body)`
  - pass through response
- Dashboard already hits `/api/hub/u/agents` → Next proxy → hub `/api/v1/u/agents` — so this closes the loop

### Commit 6 — golden snapshot build script
- `scripts/build_golden_snapshot.py`:
  1. `MorphCloudClient().instances.start({snapshotId: BASE_SNAPSHOT_ID})`
  2. `instance.exec("apt-get install postgresql-14 docker.io")`
  3. `instance.exec("sudo -u postgres createuser -s artic && createdb -O artic artic")`
  4. `instance.exec("docker pull ghcr.io/silonelabs/artic-user-server:v0")`
  5. `instance.exec("docker pull ghcr.io/silonelabs/artic-agent:v0")`
  6. `snap = instance.snapshot()` → prints `snap.id`
  7. `instance.stop()`
- Run once per release; output pasted into `.env.dev` as `MORPH_GOLDEN_SNAPSHOT_ID`

### Commit 7 — CI: build + push images
- `.github/workflows/build-images.yml`: on tag `v*`, build+push both images to ghcr w/ tag + `latest`

### Commit 8 — env + docs
- `.env.dev.example`: add `BASE_SNAPSHOT_ID`, `MORPH_GOLDEN_SNAPSHOT_ID`, `HUB_SHARED_SECRET`, `RELEASE_TAG=v0`
- Update `docs/alpha/plans/connections.md`: new `/api/v1/u/agents*` path
- Update `docs/alpha/system-map.md`: hub → Morph → user-server call graph

### Commit 9 — dev fallback (no Morph)
- `MORPH_FAKE=1` env → hub skips Morph SDK; provisions "fake VM" = spawns local user-server container in hub's Docker + publishes port
- Lets you dev without burning Morph credits

### Commit 10 — E2E smoke
- Flip dashboard `NEXT_PUBLIC_MOCK_HUB=0`
- Log in (real hub)
- Click Create Agent → Morph spawns → agent container runs
- Verify via `morph exec <instance> 'docker ps'` + hub logs showing heartbeat

## Effort

| Phase | Days (1 eng) |
|---|---|
| Images (1) + user-server (2) | 2 |
| Hub morph wrapper (3) + user_vms (4) + proxy (5) | 3 |
| Golden build (6) + CI (7) + env (8) | 1.5 |
| Dev fallback (9) + E2E (10) | 1.5 |
| **Total** | **~8 days** |

Parallelizable: images+user-server ∥ hub wrapper+proxy. 2 engs ≈ 5 days wall.

## Blockers

- Need `BASE_SNAPSHOT_ID` (Morph blank) — does Morph provide one by default or do we create via `morphvm-minimal`? I'll check via SDK on first run.
- GitHub org `silonelabs` for ghcr — need write access or alt registry
- Dashboard auth: current hub spec is wallet; dashboard uses email/password. For v0, add a trivial `POST /auth/login` to hub (email+bcrypt) alongside existing wallet flow; defer reconciliation to beta.

## Open Qs

1. Dev fallback priority — build `MORPH_FAKE=1` path (commit 9) before real Morph, or skip and test only against real Morph?
2. Email/password login on hub — add for v0 (keeps dashboard as-is) or switch dashboard to wallet sign-in (more work, more aligned w/ alpha spec)?
3. Go with `silonelabs` ghcr org or alt registry?
