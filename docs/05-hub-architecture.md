# Hub Architecture — Gap Analysis & Roadmap

## Target Vision

```
                        ┌──────────────────────┐
                        │    Central Hub        │
                        │  (Python server)      │
                        │                       │
             ┌──────────┤  REST/WS API          │
             │          │  Agent orchestration   │
             │          │  Auth + sessions       │
             │          └──────────┬─────────────┘
             │                     │
    ┌────────┴─────┐    ┌─────────┴──────────┐
    │   Clients    │    │     Agents          │
    │              │    │                     │
    │  TUI (local) │    │  Docker container 1 │ ← BTCUSDT engine
    │  CLI         │    │  Docker container 2 │ ← ETHUSDT engine
    │  Telegram    │    │  Docker container N │ ← ... engine
    │  Web (future)│    │                     │
    └──────────────┘    └─────────────────────┘
```

User connects via any client → Hub manages agents → Agents run in Docker containers.

## Current System vs Target

| Aspect | Current | Target |
|--------|---------|--------|
| **Orchestrator** | `agent_manager.py` (TUI-coupled) | Standalone hub server |
| **Client** | TUI only (hardcoded) | Pluggable: TUI, CLI, Telegram, Web |
| **Agent process** | Bare `subprocess.Popen` | Docker container per agent |
| **Communication** | Direct HTTP (TUI → agent) | Hub relays: Client → Hub → Agent |
| **Auth** | None | API keys / JWT |
| **Agent discovery** | `agents.json` file | Hub registry (DB or in-memory) |
| **Logs** | Poll `/logs` from agent | Hub aggregates + streams via WS |
| **Port management** | Sequential from 8010 | Docker port mapping or internal network |

## Gap Breakdown

### Gap 1: No Central Hub Server

**Current:** `AgentManager` is instantiated inside `BelaTUI` — it's a library, not a server. No way for external clients to reach it.

**Need:** A standalone FastAPI/WebSocket server that:
- Exposes agent CRUD (create, start, stop, delete, list)
- Proxies status/logs from agents
- Handles auth
- Runs independently of any client

**Effort:** Medium. Extract `AgentManager` logic into a new `hub/server.py`. Wrap existing methods with HTTP endpoints.

### Gap 2: No Client Abstraction

**Current:** TUI directly imports `AgentManager` and calls methods in-process.

**Need:** Clients talk to hub via HTTP/WS. Thin client SDK:

```python
class HubClient:
    def __init__(self, hub_url, api_key):
        ...
    async def create_agent(self, config) -> AgentInfo
    async def start_agent(self, agent_id) -> AgentInfo
    async def stop_agent(self, agent_id)
    async def get_status(self, agent_id) -> dict
    async def stream_logs(self, agent_id) -> AsyncIterator[dict]
    async def list_agents(self) -> list[AgentInfo]
```

TUI becomes a client. Telegram bot becomes a client. CLI becomes a client.

**Effort:** Low-Medium. The HTTP endpoints already exist on agents — hub just needs to proxy them.

### Gap 3: No Docker Containerization

**Current:** `subprocess.Popen([sys.executable, "-m", "uvicorn", ...])` — bare process, same machine.

**Need:** Each agent runs in a Docker container:

```python
# Instead of:
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", ...])

# Do:
container = docker_client.containers.run(
    "bela-agent:latest",
    ports={"8000/tcp": next_port},
    environment={"TWELVE_DATA_API_KEY": ..., "GEMINI_API_KEY": ...},
    detach=True,
)
```

**Benefits:**
- Isolation (memory, CPU limits)
- Restart policies
- Easy cleanup
- Portable across machines

**Prerequisites:**
- Dockerfile for agent image
- Docker SDK for Python (`docker` package)
- Container lifecycle management (health checks, restart, cleanup)

**Effort:** Medium. Core logic is same — just swap `Popen` for Docker API calls.

### Gap 4: No Authentication

**Current:** Agent HTTP endpoints are wide open on localhost.

**Need:**
- Hub API: API key or JWT auth
- Agent endpoints: Only hub can reach them (Docker network isolation)

**Effort:** Low. FastAPI has built-in security schemes.

### Gap 5: No WebSocket Streaming

**Current:** TUI polls `/logs` and `/status` every 2s via HTTP GET.

**Need:** Hub streams logs/status updates to connected clients via WebSocket for real-time UX.

**Effort:** Medium. FastAPI supports WebSocket. Agent-side can stay HTTP (hub polls and relays).

## Proposed Hub Architecture

```
hub/
├── server.py          # FastAPI hub server
├── agent_registry.py  # Agent state management
├── docker_manager.py  # Docker container lifecycle
├── auth.py            # API key / JWT auth
├── ws_manager.py      # WebSocket connection manager
└── client.py          # Hub client SDK

clients/
├── tui/               # Terminal UI (uses client SDK)
├── cli/               # CLI tool (uses client SDK)
└── telegram/          # Telegram bot (uses client SDK)
```

### Hub API Surface

```
POST   /api/agents              # Create agent
GET    /api/agents              # List agents
GET    /api/agents/{id}         # Get agent detail
POST   /api/agents/{id}/start   # Start agent
POST   /api/agents/{id}/stop    # Stop agent
DELETE /api/agents/{id}         # Delete agent
GET    /api/agents/{id}/status  # Proxy to agent /status
GET    /api/agents/{id}/logs    # Proxy to agent /logs
WS     /ws/agents/{id}/logs     # Stream logs via WebSocket
WS     /ws/agents/{id}/status   # Stream status via WebSocket
POST   /api/auth/login          # Get JWT token
```

### Docker Agent Lifecycle

```
Hub receives POST /api/agents
  1. Pull/build bela-agent:latest image
  2. docker.containers.run(
       image="bela-agent:latest",
       name=f"bela-agent-{agent_id}",
       ports={"8000/tcp": allocated_port},
       environment={...},
       restart_policy={"Name": "on-failure", "MaximumRetryCount": 3},
       mem_limit="512m",
     )
  3. Wait for container health check
  4. POST /start to container
  5. Register in agent_registry
```

## Implementation Roadmap

### Phase 1: Hub Server (extract from TUI)

- [ ] Create `hub/server.py` with FastAPI
- [ ] Move `AgentManager` logic to `hub/agent_registry.py`
- [ ] Add hub API endpoints (CRUD + proxy)
- [ ] Create `hub/client.py` SDK
- [ ] Refactor TUI to use client SDK instead of direct AgentManager

**Result:** TUI works via hub. Other clients can connect.

### Phase 2: Docker Agents

- [ ] Write Dockerfile for `bela-agent` image
- [ ] Create `hub/docker_manager.py`
- [ ] Replace `subprocess.Popen` with Docker API calls
- [ ] Docker network for hub ↔ agent communication
- [ ] Container health checks + restart policies

**Result:** Agents run in containers. Hub manages lifecycle.

### Phase 3: Clients

- [ ] CLI client (thin wrapper around hub SDK)
- [ ] Telegram bot client (webhook or polling mode)
- [ ] WebSocket streaming (hub aggregates + relays)

**Result:** Multiple clients can control agents.

### Phase 4: Auth + Multi-user

- [ ] API key or JWT auth on hub
- [ ] Per-user agent isolation
- [ ] Rate limiting

## Effort Estimate

| Phase | Files | Complexity |
|-------|-------|------------|
| Phase 1 (Hub) | 4-5 new files | Medium — mostly restructuring existing code |
| Phase 2 (Docker) | 2 new files + Dockerfile | Medium — swap Popen for Docker SDK |
| Phase 3 (Clients) | 3-4 new files | Low-Medium — SDK already handles heavy lifting |
| Phase 4 (Auth) | 1-2 new files | Low |

## What's Already Reusable

The entire `app/` directory is untouched — agents are already self-contained FastAPI apps:
- `app/main.py` — already has all endpoints
- `app/engine.py` — trading loop, unchanged
- `app/pyth_client.py` — price feeds, unchanged
- All strategies, LLM planning, etc — unchanged

The agent image is literally `uvicorn app.main:app` with env vars. No code changes needed inside agents.

## Key Decisions to Make

1. **Hub persistence** — SQLite? Postgres? Keep agents.json?
2. **Docker networking** — Host network (simple) or bridge network (isolated)?
3. **Telegram bot framework** — python-telegram-bot or aiogram?
4. **Auth model** — Single user (API key) or multi-user (JWT + DB)?
5. **Hub deployment** — Same machine as agents, or separate (agents on remote Docker host)?
