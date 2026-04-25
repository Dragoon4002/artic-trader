# Docs Index — Artic

Load this file when working on documentation or cross-cutting concerns.

## Cross-Repo Files

| File | Contains | When to Read |
|------|----------|-------------|
| `/docs/architecture/overview.md` | System topology, Mermaid diagram, data flow, invariants | Any architectural question |
| `/docs/architecture/data-model.md` | Postgres tables, columns, relationships, rules | Schema changes, query design |
| `/docs/connections/service-map.md` | Call graph, port map, internal endpoints, rate limits | Adding/changing service calls |
| `/docs/connections/auth-flow.md` | JWT + API key auth, internal secret, secrets encryption | Auth changes |
| `/docs/connections/env-secrets.md` | Secret resolution order, known keys, encryption rules | Env/secret changes |
| `/docs/connections/onchain.md` | Initia MiniEVM contracts, what gets logged, env vars | On-chain logging changes |

## Module-Specific Docs

| Folder | Contents |
|--------|----------|
| `/docs/hub/` | Hub endpoints, WebSocket protocol, agent lifecycle, VM provisioning |
| `/docs/app/` | Engine loop, market data, LLM planning, on-chain integration |
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
| On-chain logging | `/docs/connections/onchain.md`, `app/onchain_logger.py` |
| Deploying contracts | `/docs/connections/onchain.md` |
| VM / Morph changes | `/docs/architecture/overview.md`, `/hub/CLAUDE.md` |

## Doc Rules

- Tables over prose for technical specs
- Mermaid diagrams go in `/docs/architecture/`
- `/docs/connections/service-map.md` is source of truth — update before code
- `/docs/connections/onchain.md` must be updated before any contract change
- Never store plaintext API keys or private keys in any doc or config
