# Quarantined — migrating to user-server

Per `docs/alpha/plans/hub.md` §142-146, these modules move to user-server. Kept here inert so the hub still imports cleanly; follow-up branch deletes them once the user-server side lands.

| Module | Destination |
|--------|------------|
| `agents/` | user-server `agents/` module |
| `docker/` | user-server container orchestration |
| `agent_manager.py` | replaced by user-server agent spawner |

Routers in `agents/router.py` are **not** registered in `hub/server.py`. All `/api/v1/u/agents/*` traffic now flows through `hub/proxy/middleware.py`.
