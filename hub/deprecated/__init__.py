"""Quarantined modules awaiting migration to user-server.

Contents:
- agents/        → user-server agents/ module (per docs/alpha/plans/hub.md §142-146)
- docker/        → user-server container orchestration
- agent_manager.py → legacy subprocess spawner; remove once user-server replaces

Do NOT import from here in new code. Routers here are unregistered in server.py.
"""
