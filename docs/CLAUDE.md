# Docs Index — Artic

Load this file when working on documentation or cross-cutting concerns.

## Cross-Repo Files

| File | Contains | When to Read |
|------|----------|-------------|
| `/docs/architecture/overview.md` | System topology, Mermaid diagram, data flow, invariants | Any architectural question |
| `/docs/architecture/data-model.md` | 8 Postgres tables, columns, relationships, rules | Schema changes, query design |
| `/docs/connections/service-map.md` | Call graph, port map, internal endpoints, rate limits | Adding/changing service calls |
| `/docs/connections/auth-flow.md` | JWT + API key auth, internal secret, secrets encryption | Auth changes |
| `/docs/connections/env-secrets.md` | Secret resolution order, known keys, encryption rules | Env/secret changes |

## Module-Specific Docs

| Folder | Contents |
|--------|----------|
| `/docs/hub/` | Hub endpoints, WebSocket protocol, agent lifecycle |
| `/docs/app/` | Engine loop, market data, LLM planning |
| `/docs/strategies/` | Algorithm catalog, params, signal contract |
| `/docs/clients/tui/` | Screens, keybindings, polling |
| `/docs/clients/cli/` | Command reference, --json flag |
| `/docs/clients/telegram/` | Bot commands, message formatting |

## When to Read What

| Task | Files to Load |
|------|--------------|
| Auth change | `/docs/connections/auth-flow.md`, `/docs/connections/env-secrets.md` |
| New strategy | `/docs/strategies/`, `/app/strategies/CLAUDE.md` |
| New client | `/docs/connections/service-map.md`, relevant `/docs/clients/*/` |
| Agent lifecycle | `/docs/architecture/overview.md`, `/docs/hub/` |
| Env/secrets change | `/docs/connections/env-secrets.md` |
| DB schema change | `/docs/architecture/data-model.md` |
| New endpoint | `/docs/connections/service-map.md`, relevant module docs |
| On-chain logging | `/docs/architecture/data-model.md` (onchain_decisions table) |

## Doc Rules

- Tables over prose for technical specs
- Mermaid diagrams go in `/docs/architecture/`
- `/docs/connections/service-map.md` is source of truth — update before code
- Never store plaintext API keys in any doc or config
