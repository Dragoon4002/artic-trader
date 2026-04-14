# TUI Guide

## Quick Start

```bash
cd bela-quant-engine
pip install -r requirements.txt
cp .env.example .env   # edit with your API keys
python tui.py
```

Minimum env: `TWELVE_DATA_API_KEY` + one LLM key (`GEMINI_API_KEY`, `OPENAI_API_KEY`, etc).

## Screens

### Dashboard (home)

Master-detail layout: agent list on left, live status on right.

```
┌─ Agents ──────────┐┌─ Status ──────────────────────┐
│ ● BTC Agent  8010 ││ BTCUSDT | LONG @ $72,100      │
│ ○ ETH Agent  8011 ││ PnL: +$25.00 | Strategy: ema  │
│ ○ SOL Agent  ---  ││ Last tick: HOLD (signal weak)  │
└───────────────────┘└──────────────────────────────────┘
```

- `●` = alive, `○` = stopped
- Status auto-refreshes every 2s

### Create Agent (n)

Form wizard for new agent:

| Field | Default | Options |
|-------|---------|---------|
| Name | auto | free text |
| Symbol | BTCUSDT | any trading pair |
| Amount USDT | 1000 | numeric |
| Leverage | 5 | 1-150 |
| Risk profile | moderate | conservative/moderate/aggressive |
| Timeframe | 15m | 1m/5m/15m/30m/1h/4h/1d |
| Poll seconds | 1.0 | numeric |
| TP % | 0 (auto) | numeric |
| SL % | 0 (auto) | numeric |
| TP/SL mode | fixed | fixed/dynamic |
| Supervisor interval | 60s | numeric |
| LLM provider | auto | openai/anthropic/deepseek/gemini |
| Per-agent API keys | inherit .env | optional override |

### Log Viewer (l)

Live log stream with filter/search:

- Agent dropdown (only shows alive agents)
- Level filter: ALL, Init, LLM, Tick, Action, Error, Supervisor
- Text search
- Auto-scroll toggle
- Polls every 2s

### Theme (t)

5 themes: hacker-green, cyber-finance, neon, midnight, vapor

## Keybindings

| Key | Screen | Action |
|-----|--------|--------|
| `n` | Dashboard | Create new agent |
| `f` | Dashboard | Start all stopped agents |
| `g` | Dashboard | Stop all running agents |
| `s` | Dashboard | Start selected agent |
| `x` | Dashboard | Stop selected agent |
| `d` | Dashboard | Delete selected agent |
| `l` | Dashboard | Open log viewer |
| `t` | Dashboard | Change theme |
| `q` | Any | Quit |
| `Esc` | Sub-screen | Back to dashboard |

## How Agents Work

1. TUI creates an `AgentInfo` with config
2. `AgentManager.launch()` spawns a `uvicorn` subprocess on port 8010+
3. Waits for `/health` to return 200 (15s timeout)
4. POSTs to `/start` with the trading config
5. Engine begins: fetches price from Pyth, plans strategy via LLM, enters tick loop
6. TUI polls `/status` and `/logs` every 2s

Each agent is fully isolated — own process, own port, own trading engine instance.

## Port Assignment

Base port: 8010. Each new agent gets next available port. Ports recycle when agents stop.

**Known issue:** Starting all agents simultaneously (`f` key) can cause port collisions due to race condition in `_next_port()`. Workaround: start agents one at a time.

## Config Persistence

- `~/.arcgenesis/agents.json` — all agent configs (survives TUI restart)
- API keys are **not** persisted (memory-only per session)
- On TUI start, all agents load as `alive=False` and must be restarted

## Troubleshooting

**No logs showing:**
- Agent must be alive (started via TUI, not manual uvicorn)
- `/start` must have been called (engine must be running)
- Check log level filter isn't hiding entries

**Agent won't start:**
- Check `TWELVE_DATA_API_KEY` is set
- Check at least one LLM key is set
- Check port isn't already in use: `ss -tlnp | grep 801`

**Stale processes:**
- `pkill -f 'uvicorn app.main'` to kill orphaned agents
- Delete stale entries from `~/.arcgenesis/agents.json`
