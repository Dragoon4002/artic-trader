#!/usr/bin/env python3
"""Artic CLI — interactive session-based interface."""
import asyncio
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()
from hub.client import HubClient

TOKEN_FILE = os.path.expanduser("~/.artic/token")


def _load_token() -> str | None:
    try:
        return open(TOKEN_FILE).read().strip()
    except FileNotFoundError:
        return None


def _save_token(token: str):
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token)


def _clear_token():
    try:
        os.remove(TOKEN_FILE)
    except FileNotFoundError:
        pass


def _make_client(token: str) -> HubClient:
    hub_url = os.getenv("ARTIC_HUB_URL", "http://localhost:8000")
    return HubClient(base_url=hub_url, token=token)


# ── Input helpers ──────────────────────────────────────────────

def prompt(msg: str, default=None, hint: str | None = None) -> str:
    if hint:
        suffix = f" [{hint}]"
    elif default is not None:
        suffix = f" [{default}]"
    else:
        suffix = ""
    val = input(f"{msg}{suffix}: ").strip()
    return val if val else (str(default) if default is not None else "")


def pick(title: str, options: list[str]) -> int | None:
    """Show numbered list, return 0-based index or None on cancel."""
    if not options:
        print("  (none)")
        return None
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    raw = input("> ").strip()
    if not raw:
        return None
    try:
        idx = int(raw)
        if 1 <= idx <= len(options):
            return idx - 1
    except ValueError:
        pass
    print("Invalid choice.")
    return None


# ── Auth ───────────────────────────────────────────────────────

async def auth_flow() -> str | None:
    """Login or register. Returns JWT token or None."""
    hub_url = os.getenv("ARTIC_HUB_URL", "http://localhost:8000")
    client = HubClient(base_url=hub_url)

    print("\n=== Artic CLI ===")
    print("  [1] Login")
    print("  [2] Register")
    print("  [0] Exit")
    choice = input("> ").strip()

    if choice == "0":
        return None

    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    try:
        if choice == "1":
            token = await client.login(email, password)
            print("Logged in.")
        elif choice == "2":
            token = await client.register(email, password)
            print("Registered and logged in.")
        else:
            print("Invalid choice.")
            return await auth_flow()
        _save_token(token)
        return token
    except Exception as e:
        print(f"Error: {e}")
        return await auth_flow()


# ── Agent formatting ───────────────────────────────────────────

def _fmt_status(status: str) -> str:
    s = status.lower()
    if s in ("alive", "running"):
        return "RUNNING"
    if s == "stopped":
        return "STOPPED"
    return status.upper()


def _fmt_agent_line(a: dict, idx: int | None = None) -> str:
    icon = "●" if a.get("status", "").lower() in ("alive", "running") else "○"
    name = a.get("name", "?")[:20]
    symbol = a.get("symbol", "?")
    status = _fmt_status(a.get("status", "?"))
    llm = a.get("llm_provider") or "-"
    aid = a.get("id", "?")[:8]
    prefix = f"  [{idx}]" if idx is not None else "  "
    return f"{prefix} {icon} {name:<20} {symbol:<10} {status:<10} {llm:<12} {aid}"


# ── Agent picker (reused by start/stop/status/logs/delete/edit) ─

async def pick_agent(client: HubClient) -> str | None:
    """Fetch agents, show indexed list, return selected agent_id."""
    try:
        agents = await client.list_agents()
    except Exception as e:
        print(f"Error fetching agents: {e}")
        return None

    if not agents:
        print("  No agents found.")
        return None

    for i, a in enumerate(agents, 1):
        print(_fmt_agent_line(a, idx=i))
    raw = input("> ").strip()
    if not raw:
        return None
    try:
        idx = int(raw)
        if 1 <= idx <= len(agents):
            return agents[idx - 1]["id"]
    except ValueError:
        pass
    print("Invalid choice.")
    return None


# ── Menu handlers ─────────────────────────────────────────────

async def do_list_agents(client: HubClient):
    try:
        agents = await client.list_agents()
    except Exception as e:
        print(f"Error: {e}")
        return
    if not agents:
        print("  No agents.")
        return
    print(f"\n    {'NAME':<22} {'SYMBOL':<10} {'STATUS':<10} {'LLM':<12} ID")
    print("  " + "-" * 68)
    for a in agents:
        print(_fmt_agent_line(a))


async def do_create_agent(client: HubClient):
    print("\n--- Create Agent ---")
    symbol = prompt("Symbol", hint="e.g. BTCUSDT, required")
    if not symbol:
        print("Symbol required.")
        return

    name = prompt("Name", hint=f"Enter name, empty = '{symbol.upper()} Agent'")
    name = name or f"{symbol.upper()} Agent"
    amount = float(prompt("Amount USDT", hint="Enter number, empty = 100") or "100")
    leverage = int(prompt("Leverage", hint="1-125, empty = 5") or "5")

    print("  Risk: 1=aggressive  2=moderate  3=conservative")
    risk_raw = prompt("Risk profile", hint="1/2/3, empty = 2")
    risk_map = {"1": "aggressive", "2": "moderate", "3": "conservative"}
    risk = risk_map.get(risk_raw, "moderate")

    print("  Timeframes: 1=1m  2=5m  3=15m  4=30m  5=1h  6=4h  7=1d")
    tf_raw = prompt("Timeframe", hint="1-7, empty = 3 (15m)")
    tf_map = {"1": "1m", "2": "5m", "3": "15m", "4": "30m", "5": "1h", "6": "4h", "7": "1d"}
    timeframe = tf_map.get(tf_raw, "15m")

    tp_raw = prompt("Take profit %", hint="Enter number, empty = skip")
    sl_raw = prompt("Stop loss %", hint="Enter number, empty = skip")
    live_raw = prompt("Live mode?", hint="y/n, empty = n")

    print("  LLM: 1=openai  2=anthropic  3=deepseek  4=gemini")
    llm_raw = prompt("LLM provider", hint="1-4, empty = skip")
    llm_map = {"1": "openai", "2": "anthropic", "3": "deepseek", "4": "gemini"}
    llm = llm_map.get(llm_raw)

    auto_start_raw = prompt("Auto start?", hint="y/n, empty = y")

    kwargs = {
        "symbol": symbol.upper(),
        "name": name,
        "amount_usdt": amount,
        "leverage": leverage,
        "risk_profile": risk,
        "primary_timeframe": timeframe,
        "live_mode": (live_raw or "n").lower() == "y",
    }
    if tp_raw:
        kwargs["tp_pct"] = float(tp_raw) / 100.0
    if sl_raw:
        kwargs["sl_pct"] = float(sl_raw) / 100.0
    if llm:
        kwargs["llm_provider"] = llm
        llm_key = getpass.getpass("LLM API key: ")
        if llm_key:
            kwargs["llm_api_key"] = llm_key
    if (auto_start_raw or "y").lower() == "n":
        kwargs["auto_start"] = False

    try:
        result = await client.create_agent(**kwargs)
        aid = result.get("id", "?")[:8]
        status = result.get("status", "?")
        print(f"Agent {result.get('name')} ({aid}) — {status}")
        if result.get("error"):
            print(f"  Spawn failed: {result['error']}")
    except Exception as e:
        print(f"Error: {e}")


async def do_start_agent(client: HubClient):
    print("\n--- Start Agent ---")
    agent_id = await pick_agent(client)
    if not agent_id:
        return
    try:
        result = await client.start_agent(agent_id)
        print(f"Agent {result.get('name')} — {result.get('status')}")
    except Exception as e:
        print(f"Error: {e}")


async def do_stop_agent(client: HubClient):
    print("\n--- Stop Agent ---")
    agent_id = await pick_agent(client)
    if not agent_id:
        return
    try:
        result = await client.stop_agent(agent_id)
        print(f"Stopped. Status: {result.get('status', result)}")
    except Exception as e:
        print(f"Error: {e}")


async def do_agent_status(client: HubClient):
    print("\n--- Agent Status ---")
    agent_id = await pick_agent(client)
    if not agent_id:
        return
    try:
        result = await client.get_status(agent_id)
        if result.get("error"):
            print(f"  ** {result['error']} **")
        for k, v in result.items():
            if k in ("error", "stale"):
                continue
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error: {e}")


async def do_agent_logs(client: HubClient):
    print("\n--- Agent Logs ---")
    agent_id = await pick_agent(client)
    if not agent_id:
        return
    limit = int(prompt("Number of log lines", 50))
    try:
        logs = await client.get_logs(agent_id, limit=limit)
        for entry in logs:
            ts = entry.get("timestamp", "")
            lvl = entry.get("level", "")
            msg = entry.get("message", "")
            print(f"  {ts}  {lvl:<12} {msg}")
    except Exception as e:
        print(f"Error: {e}")


async def do_delete_agent(client: HubClient):
    print("\n--- Delete Agent ---")
    agent_id = await pick_agent(client)
    if not agent_id:
        return
    confirm = input(f"Delete {agent_id[:8]}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    try:
        await client.delete_agent(agent_id)
        print(f"Deleted {agent_id[:8]}")
    except Exception as e:
        print(f"Error: {e}")


async def do_edit_agent(client: HubClient):
    print("\n--- Edit Agent ---")
    agent_id = await pick_agent(client)
    if not agent_id:
        return

    print("Press Enter to skip any field.\n")
    updates = {}

    v = prompt("Name", hint="Enter new name, empty = skip")
    if v:
        updates["name"] = v

    v = prompt("Amount USDT", hint="Enter number, empty = skip")
    if v:
        updates["amount_usdt"] = float(v)

    v = prompt("Leverage", hint="1-125, empty = skip")
    if v:
        updates["leverage"] = int(v)

    print("  Risk: 1=aggressive  2=moderate  3=conservative")
    v = prompt("Risk profile", hint="1/2/3, empty = skip")
    risk_map = {"1": "aggressive", "2": "moderate", "3": "conservative"}
    if v and v in risk_map:
        updates["risk_profile"] = risk_map[v]

    v = prompt("TP %", hint="Enter number, empty = skip")
    if v:
        updates["tp_pct"] = float(v) / 100.0

    v = prompt("SL %", hint="Enter number, empty = skip")
    if v:
        updates["sl_pct"] = float(v) / 100.0

    print("  LLM: 1=openai  2=anthropic  3=deepseek  4=gemini")
    v = prompt("LLM provider", hint="1-4, empty = skip")
    llm_map = {"1": "openai", "2": "anthropic", "3": "deepseek", "4": "gemini"}
    if v and v in llm_map:
        updates["llm_provider"] = llm_map[v]

    if not updates:
        print("No changes.")
        return

    try:
        result = await client.edit_agent(agent_id, **updates)
        print(f"Updated. Status: {result.get('status')}")
        for field in updates:
            print(f"  {field}: {result.get(field)}")
    except Exception as e:
        print(f"Error: {e}")


async def do_kill_all(client: HubClient):
    confirm = input("Kill ALL agents? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    try:
        result = await client.kill_all()
        print(f"Stopped {result.get('stopped', 0)}/{result.get('total', 0)} agents")
    except Exception as e:
        print(f"Error: {e}")


async def do_leaderboard(client: HubClient):
    print("\n--- Leaderboard ---")
    limit = int(prompt("Limit", 10))
    sort_by = prompt("Sort by (total_pnl/win_rate/sharpe/trade_count)", "total_pnl")
    symbol = prompt("Filter symbol", "skip")

    try:
        data = await client.get_leaderboard(
            limit=limit, sort_by=sort_by,
            symbol=symbol.upper() if symbol != "skip" else None,
        )
        entries = data.get("leaderboard", [])
        if not entries:
            print("  No agents on leaderboard yet.")
            return

        print(f"\n  {'RANK':<6} {'AGENT':<18} {'SYMBOL':<10} {'OWNER':<14} "
              f"{'TRADES':<8} {'PNL':>10} {'WIN%':>7} {'SHARPE':>8} STATUS")
        print("  " + "-" * 95)
        for e in entries:
            pnl = e["total_pnl_usdt"]
            pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            dot = "●" if e["is_running"] else "○"
            print(
                f"  {e['rank']:<6} {e['agent_name'][:17]:<18} {e['symbol']:<10} "
                f"{e['owner'][:13]:<14} {e['total_trades']:<8} {pnl_str:>10} "
                f"{e['win_rate']*100:>6.1f}% {e['sharpe_ratio']:>8.2f} "
                f"{dot} {e['status']}"
            )
        print(f"\n  {data['total_agents']} agents competing globally")
    except Exception as e:
        print(f"Error: {e}")


# ── Main menu loop ────────────────────────────────────────────

MENU = """
=== Main Menu ===
  [1]  List agents
  [2]  Create agent
  [3]  Start agent
  [4]  Stop agent
  [5]  Agent status
  [6]  Agent logs
  [7]  Delete agent
  [8]  Edit agent
  [9]  Kill all agents
  [10] Leaderboard
  [0]  Exit"""

HANDLERS = {
    "1": do_list_agents,
    "2": do_create_agent,
    "3": do_start_agent,
    "4": do_stop_agent,
    "5": do_agent_status,
    "6": do_agent_logs,
    "7": do_delete_agent,
    "8": do_edit_agent,
    "9": do_kill_all,
    "10": do_leaderboard,
}


async def main_loop():
    token = _load_token()

    # If no saved token, run auth flow
    if not token:
        token = await auth_flow()
        if not token:
            print("Bye.")
            return

    client = _make_client(token)

    # Verify token works
    try:
        await client.list_agents()
    except Exception:
        print("Session expired. Please login again.")
        _clear_token()
        token = await auth_flow()
        if not token:
            return
        client = _make_client(token)

    while True:
        print(MENU)
        choice = input("> ").strip()

        if choice == "0":
            _clear_token()
            print("Logged out. Bye.")
            break

        handler = HANDLERS.get(choice)
        if handler:
            try:
                await handler(client)
            except KeyboardInterrupt:
                print("\nCancelled.")
            except EOFError:
                print("\nBye.")
                break
        else:
            print("Invalid choice.")


def main():
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nBye.")


if __name__ == "__main__":
    main()
