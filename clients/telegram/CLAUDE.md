# Telegram Client — Artic

Telegram bot for agent monitoring and control via messages.

## Key Files (TODO)

| File | Purpose |
|------|---------|
| bot.py | Entry point, webhook registration |
| handlers/ | Command handler modules |
| formatter.py | Telegram markdown formatting |

## Calls Into

Hub only, via `/hub/client.py` SDK.

## Conventions

- Commands mirror hub SDK methods 1:1
- Never expose raw logs — summarise only
- Bot token in USER_SECRETS, never hardcoded
