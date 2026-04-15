"""Telegram message formatting utilities."""


def format_agent_card(agent: dict) -> str:
    """Format agent dict for Telegram."""
    status = "🟢" if agent.get("status") == "alive" else "🔴"
    return f"{status} `{agent['id'][:8]}` — {agent.get('symbol', '?')}"


def format_status(status: dict) -> str:
    """Format StatusResponse for Telegram."""
    pnl = status.get("unrealized_pnl_usdt", 0) or 0
    emoji = "📈" if pnl >= 0 else "📉"
    return (
        f"*{status.get('symbol', '?')}* {emoji}\n"
        f"Side: {status.get('side', 'FLAT')}\n"
        f"Price: ${status.get('last_price', 0):,.2f}\n"
        f"PnL: {pnl:+.2f} USDT\n"
        f"Strategy: {status.get('active_strategy', '?')}"
    )


def format_log_summary(logs: list) -> str:
    """Summarize logs — never expose raw content."""
    actions = sum(1 for l in logs if l.get("level") in ("action", "sl_tp"))
    errors = sum(1 for l in logs if l.get("level") == "error")
    supervisor = sum(1 for l in logs if l.get("level") == "supervisor")
    return (
        f"📊 Log Summary ({len(logs)} entries)\n"
        f"  Actions: {actions}\n"
        f"  Supervisor: {supervisor}\n"
        f"  Errors: {errors}"
    )
