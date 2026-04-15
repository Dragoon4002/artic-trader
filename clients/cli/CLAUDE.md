# CLI Client — Artic

Thin CLI wrapper around hub SDK for scripting and automation.

## Key Files (TODO)

| File | Purpose |
|------|---------|
| cli.py | Entry point, argument parsing |
| commands/ | Subcommand modules |

## Calls Into

Hub only, via `/hub/client.py` SDK.

## Conventions

- Every command must have `--json` flag for machine-readable output
- No interactive prompts in non-TTY mode
