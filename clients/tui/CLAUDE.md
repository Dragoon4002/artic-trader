# TUI Client — Artic

Textual terminal UI. Thin client — all state lives in the hub.

## Key Files

| File | Purpose |
|------|---------|
| tui.py | Main app, 5 screens (Dashboard, CreateAgent, LogViewer, Theme, AgentDetail) |

## Calls Into

Hub only, via `/hub/client.py` SDK — never directly to app containers.

## Docs → `/docs/clients/tui/` | Keybindings: `/docs/clients/tui/keybindings.md`

## Conventions

- All hub calls go through `HubClient` — no raw httpx in screen code
- Poll interval: 2s
