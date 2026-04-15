"""Artic Telegram bot — agent monitoring via chat."""
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters,
)
from hub.client import HubClient
from hub.utils.symbols import _SYMBOL_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("artic.telegram")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
HUB_URL = os.getenv("ARTIC_HUB_URL", "http://localhost:8000")

_clients: dict[int, HubClient] = {}


def _get_client(chat_id: int) -> HubClient | None:
    return _clients.get(chat_id)


def _reply(update: Update):
    return update.effective_message


async def _resolve_agent_id(client: HubClient, prefix: str, msg) -> str | None:
    if len(prefix) < 4:
        await msg.reply_text("Agent ID prefix must be at least 4 characters.")
        return None
    agents = await client.list_agents()
    matches = [a for a in agents if a["id"].startswith(prefix)]
    if len(matches) == 1:
        return matches[0]["id"]
    if len(matches) == 0:
        await msg.reply_text(f"No agent found matching {prefix}.")
        return None
    lines = ["Multiple agents match, be more specific:"]
    for a in matches:
        lines.append(f"  {a['id'][:12]} — {a.get('symbol', '?')}")
    await msg.reply_text("\n".join(lines))
    return None


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _reply(update).reply_text(
        "Welcome to Artic Trading Bot!\n\n"
        "Commands:\n"
        "/register <email> <password>\n"
        "/login <email> <password>\n"
        "/agents — list agents with PnL\n"
        "/agent <agent_id> — full agent details\n"
        "/status <agent_id> — live status\n"
        "/symbols — supported trading pairs\n"
        "/create — create agent (guided setup)\n"
        "/cancel — cancel agent creation\n"
        "/startbot <agent_id> — restart agent\n"
        "/stopbot <agent_id> — stop agent\n"
        "/edit <agent_id> <field> <value> — edit config\n"
        "/logs <agent_id> — recent logs\n"
        "/leaderboard — global rankings\n"
        "/optin <agent_id> [handle] — join leaderboard\n"
        "/optout <agent_id> — leave leaderboard\n"
    )


async def cmd_register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = _reply(update)
    args = ctx.args
    if len(args) < 2:
        await msg.reply_text("Usage: /register <email> <password>")
        return
    client = HubClient(base_url=HUB_URL)
    try:
        await client.register(args[0], args[1])
        _clients[update.effective_chat.id] = client
        await msg.reply_text("Account created & logged in.")
    except Exception as e:
        await msg.reply_text(f"Registration failed: {e}")


async def cmd_login(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = _reply(update)
    args = ctx.args
    if len(args) < 2:
        await msg.reply_text("Usage: /login <email> <password>")
        return
    client = HubClient(base_url=HUB_URL)
    try:
        await client.login(args[0], args[1])
        _clients[update.effective_chat.id] = client
        await msg.reply_text("Logged in successfully.")
    except Exception as e:
        await msg.reply_text(f"Login failed: {e}")


async def cmd_agents(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in. Use /login first.")
        return
    try:
        agents = await client.list_agents()
        if not agents:
            await msg.reply_text("No agents found.")
            return
        lines = []
        for a in agents:
            emoji = "\U0001f7e2" if a.get("status") == "alive" else "\U0001f534"
            aid = a.get("id", "?")[:8]
            name = a.get("name", "?")
            symbol = a.get("symbol", "?")
            # fetch PnL for alive agents
            pnl_str = ""
            if a.get("status") == "alive":
                try:
                    st = await client.get_status(a["id"])
                    pnl = st.get("unrealized_pnl_usdt") or 0
                    stale = " \u26a0\ufe0f" if st.get("error") else ""
                    pnl_str = f" | PnL: {pnl:+.2f}{stale}"
                except Exception:
                    pnl_str = " | PnL: N/A"
            lines.append(f"{emoji} {aid} {name} — {symbol}{pnl_str}")
        await msg.reply_text("\n".join(lines))
    except Exception as e:
        await msg.reply_text(f"Error: {e}")


async def cmd_agent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Show full details for a single agent. /agent <agent_id>"""
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /agent <agent_id>")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    try:
        a = await client.get_agent(agent_id)
        aid = a.get("id", "?")[:8]
        emoji = "\U0001f7e2" if a.get("status") == "alive" else "\U0001f534"
        text = (
            f"{emoji} {a.get('name', '?')}\n"
            f"ID: {aid}\n"
            f"Symbol: {a.get('symbol', '?')}\n"
            f"Status: {a.get('status', '?')}\n"
            f"Amount: {a.get('amount_usdt', '?')} USDT\n"
            f"Leverage: {a.get('leverage', '?')}x\n"
            f"Risk: {a.get('risk_profile', '?')}\n"
            f"TP/SL: {a.get('tp_pct', '-')}/{a.get('sl_pct', '-')} ({a.get('tp_sl_mode', '?')})\n"
            f"LLM: {a.get('llm_provider', 'default')}"
        )
        # append live status if running
        if a.get("status") == "alive":
            try:
                st = await client.get_status(agent_id)
                pnl = st.get("unrealized_pnl_usdt") or 0
                pnl_emoji = "\U0001f4c8" if pnl >= 0 else "\U0001f4c9"
                header = "\u26a0\ufe0f Stale (agent unreachable)" if st.get("error") else "Live"
                text += (
                    f"\n\n{pnl_emoji} {header}\n"
                    f"Side: {st.get('side', 'FLAT')}\n"
                    f"Price: ${(st.get('last_price') or 0):,.2f}\n"
                    f"Entry: ${(st.get('entry_price') or 0):,.2f}\n"
                    f"PnL: {pnl:+.2f} USDT\n"
                    f"Strategy: {st.get('active_strategy', '?')}\n"
                    f"Action: {st.get('last_action', 'HOLD')}"
                )
            except Exception:
                text += "\n\nLive status unavailable"
        await msg.reply_text(text)
    except Exception as e:
        await msg.reply_text(f"Error: {e}")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /status <agent_id>")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    try:
        st = await client.get_status(agent_id)
        pnl = st.get("unrealized_pnl_usdt") or 0
        price = st.get("last_price") or 0
        entry = st.get("entry_price") or 0
        pnl_emoji = "\U0001f4c8" if pnl >= 0 else "\U0001f4c9"
        stale_banner = "\u26a0\ufe0f Agent unreachable — last known state:\n\n" if st.get("error") else ""
        text = (
            f"{stale_banner}"
            f"{st.get('symbol', '?')} {pnl_emoji}\n"
            f"Side: {st.get('side', 'FLAT')}\n"
            f"Price: ${price:,.2f}\n"
            f"Entry: ${entry:,.2f}\n"
            f"PnL: {pnl:+.2f} USDT\n"
            f"Strategy: {st.get('active_strategy', '?')}\n"
            f"Action: {st.get('last_action', 'HOLD')}"
        )
        await msg.reply_text(text)
    except Exception as e:
        await msg.reply_text(f"Error: {e}")


async def cmd_symbols(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """List all supported trading symbols."""
    # dedupe to unique pairs
    pairs = sorted(set(_SYMBOL_MAP.values()))
    lines = ["\U0001f4b1 Supported Symbols\n"]
    for p in pairs:
        base = p.replace("USDT", "")
        lines.append(f"  {base} \u2192 {p}")
    lines.append(f"\nYou can also type the full pair (e.g. BTCUSDT) or just the ticker (e.g. BTC).")
    await _reply(update).reply_text("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════
# Create Agent — ConversationHandler (multi-step with inline keyboards)
# ═══════════════════════════════════════════════════════════════════════════

(CR_SYMBOL, CR_NAME, CR_AMOUNT, CR_LEVERAGE, CR_RISK, CR_TIMEFRAME,
 CR_TP, CR_SL, CR_LLM, CR_LLM_KEY, CR_LIVE, CR_CONFIRM) = range(12)

_POPULAR_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT",
]


def _kbd(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """Build InlineKeyboardMarkup from rows of (label, callback_data) tuples."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=data) for label, data in row]
        for row in rows
    ])


async def create_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    client = _get_client(update.effective_chat.id)
    if not client:
        await _reply(update).reply_text("Not logged in. Use /login first.")
        return ConversationHandler.END

    ctx.user_data["create"] = {}
    rows = []
    for i in range(0, len(_POPULAR_SYMBOLS), 3):
        row = [(s.replace("USDT", ""), f"sym:{s}") for s in _POPULAR_SYMBOLS[i:i+3]]
        rows.append(row)
    rows.append([("Other (type it)", "sym:OTHER")])
    await _reply(update).reply_text("Select token:", reply_markup=_kbd(rows))
    return CR_SYMBOL


async def create_symbol_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    val = q.data.removeprefix("sym:")
    if val == "OTHER":
        await q.edit_message_text("Type the symbol (e.g. PEPEUSDT):")
        return CR_SYMBOL  # wait for text
    ctx.user_data["create"]["symbol"] = val
    await q.edit_message_text(f"Symbol: {val}\n\nName for this agent? (or /skip for default)")
    return CR_NAME


async def create_symbol_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    symbol = update.message.text.strip().upper()
    ctx.user_data["create"]["symbol"] = symbol
    await update.message.reply_text(f"Symbol: {symbol}\n\nName for this agent? (or /skip for default)")
    return CR_NAME


async def create_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    d = ctx.user_data["create"]
    if text.lower() != "/skip" and text:
        d["name"] = text
    await update.message.reply_text("Amount in USDT? (or /skip for 100)")
    return CR_AMOUNT


async def create_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    d = ctx.user_data["create"]
    if text.lower() != "/skip" and text:
        try:
            d["amount_usdt"] = float(text)
        except ValueError:
            await update.message.reply_text("Invalid number. Try again or /skip:")
            return CR_AMOUNT
    await update.message.reply_text("Leverage? 1-125 (or /skip for 5)")
    return CR_LEVERAGE


async def create_leverage(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    d = ctx.user_data["create"]
    if text.lower() != "/skip" and text:
        try:
            lev = int(text)
            if lev < 1 or lev > 125:
                await update.message.reply_text("Must be 1-125. Try again:")
                return CR_LEVERAGE
            d["leverage"] = lev
        except ValueError:
            await update.message.reply_text("Invalid number. Try again or /skip:")
            return CR_LEVERAGE
    kb = _kbd([
        [("Conservative", "risk:conservative"), ("Moderate", "risk:moderate")],
        [("Aggressive", "risk:aggressive")],
    ])
    await update.message.reply_text("Risk profile:", reply_markup=kb)
    return CR_RISK


async def create_risk(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    val = q.data.removeprefix("risk:")
    ctx.user_data["create"]["risk_profile"] = val
    kb = _kbd([
        [("1m", "tf:1m"), ("5m", "tf:5m"), ("15m", "tf:15m"), ("30m", "tf:30m")],
        [("1h", "tf:1h"), ("4h", "tf:4h"), ("1d", "tf:1d")],
    ])
    await q.edit_message_text(f"Risk: {val}\n\nTimeframe:", reply_markup=kb)
    return CR_TIMEFRAME


async def create_timeframe(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    val = q.data.removeprefix("tf:")
    ctx.user_data["create"]["primary_timeframe"] = val
    await q.edit_message_text(f"Timeframe: {val}\n\nTake profit %? (e.g. 5 for 5%)\nOr /skip:")
    return CR_TP


async def create_tp(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    d = ctx.user_data["create"]
    if text.lower() != "/skip" and text:
        try:
            d["tp_pct"] = float(text) / 100
        except ValueError:
            await update.message.reply_text("Invalid number. Try again or /skip:")
            return CR_TP
    await update.message.reply_text("Stop loss %? (e.g. 2 for 2%)\nOr /skip:")
    return CR_SL


async def create_sl(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    d = ctx.user_data["create"]
    if text.lower() != "/skip" and text:
        try:
            d["sl_pct"] = float(text) / 100
        except ValueError:
            await update.message.reply_text("Invalid number. Try again or /skip:")
            return CR_SL
    kb = _kbd([
        [("OpenAI", "llm:openai"), ("Anthropic", "llm:anthropic")],
        [("Gemini", "llm:gemini"), ("DeepSeek", "llm:deepseek")],
        [("Skip", "llm:SKIP")],
    ])
    await update.message.reply_text("LLM provider:", reply_markup=kb)
    return CR_LLM


async def create_llm(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    val = q.data.removeprefix("llm:")
    d = ctx.user_data["create"]
    if val != "SKIP":
        d["llm_provider"] = val
        await q.edit_message_text(f"LLM: {val}\n\nLLM API key? (or /skip to use server default):")
        return CR_LLM_KEY
    await q.edit_message_text("LLM: server default")
    kb = _kbd([
        [("Paper Trading", "live:false"), ("Live (Pancake Perps)", "live:true")],
    ])
    await q.message.reply_text("Execution mode:", reply_markup=kb)
    return CR_LIVE


async def create_llm_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    d = ctx.user_data["create"]
    if text.lower() != "/skip" and text:
        d["llm_api_key"] = text
    kb = _kbd([
        [("Paper Trading", "live:false"), ("Live (Pancake Perps)", "live:true")],
    ])
    await update.message.reply_text("Execution mode:", reply_markup=kb)
    return CR_LIVE


async def create_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    val = q.data.removeprefix("live:")
    d = ctx.user_data["create"]
    d["live_mode"] = val == "true"

    # show summary + confirm
    sym = d.get("symbol", "?")
    lines = [
        f"Ready to launch:\n",
        f"Symbol: {sym}",
        f"Name: {d.get('name', f'{sym} Agent')}",
        f"Amount: {d.get('amount_usdt', 100)} USDT",
        f"Leverage: {d.get('leverage', 5)}x",
        f"Risk: {d.get('risk_profile', 'moderate')}",
        f"Timeframe: {d.get('primary_timeframe', '15m')}",
    ]
    if d.get("tp_pct"):
        lines.append(f"TP: {d['tp_pct']*100:.1f}%")
    if d.get("sl_pct"):
        lines.append(f"SL: {d['sl_pct']*100:.1f}%")
    lines.append(f"LLM: {d.get('llm_provider', 'default')}")
    lines.append(f"Mode: {'LIVE' if d.get('live_mode') else 'Paper'}")

    kb = _kbd([[("Launch", "confirm:yes"), ("Cancel", "confirm:no")]])
    await q.edit_message_text("\n".join(lines), reply_markup=kb)
    return CR_CONFIRM


async def create_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    if q.data == "confirm:no":
        await q.edit_message_text("Cancelled.")
        ctx.user_data.pop("create", None)
        return ConversationHandler.END

    d = ctx.user_data.pop("create", {})
    client = _get_client(update.effective_chat.id)
    if not client:
        await q.edit_message_text("Session expired. /login again.")
        return ConversationHandler.END

    try:
        result = await client.create_agent(
            symbol=d.get("symbol", "BTCUSDT"),
            name=d.get("name", f"{d.get('symbol', 'BTCUSDT')} Agent"),
            amount_usdt=d.get("amount_usdt", 100.0),
            leverage=d.get("leverage", 5),
            risk_profile=d.get("risk_profile", "moderate"),
            primary_timeframe=d.get("primary_timeframe", "15m"),
            tp_pct=d.get("tp_pct"),
            sl_pct=d.get("sl_pct"),
            live_mode=d.get("live_mode", False),
            llm_provider=d.get("llm_provider"),
            llm_api_key=d.get("llm_api_key"),
        )
        name = result.get("name", "?")
        aid = result.get("id", "?")[:8]
        status = result.get("status", "?")
        await q.edit_message_text(f"Agent {name} launched\n{d.get('symbol')} | {status} | ID: {aid}")
    except Exception as e:
        await q.edit_message_text(f"Launch failed: {e}")
    return ConversationHandler.END


async def create_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.pop("create", None)
    await _reply(update).reply_text("Agent creation cancelled.")
    return ConversationHandler.END


def _build_create_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("create", create_start)],
        states={
            CR_SYMBOL: [
                CallbackQueryHandler(create_symbol_cb, pattern=r"^sym:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_symbol_text),
            ],
            CR_NAME: [MessageHandler(filters.TEXT, create_name)],
            CR_AMOUNT: [MessageHandler(filters.TEXT, create_amount)],
            CR_LEVERAGE: [MessageHandler(filters.TEXT, create_leverage)],
            CR_RISK: [CallbackQueryHandler(create_risk, pattern=r"^risk:")],
            CR_TIMEFRAME: [CallbackQueryHandler(create_timeframe, pattern=r"^tf:")],
            CR_TP: [MessageHandler(filters.TEXT, create_tp)],
            CR_SL: [MessageHandler(filters.TEXT, create_sl)],
            CR_LLM: [CallbackQueryHandler(create_llm, pattern=r"^llm:")],
            CR_LLM_KEY: [MessageHandler(filters.TEXT, create_llm_key)],
            CR_LIVE: [CallbackQueryHandler(create_live, pattern=r"^live:")],
            CR_CONFIRM: [CallbackQueryHandler(create_confirm, pattern=r"^confirm:")],
        },
        fallbacks=[CommandHandler("cancel", create_cancel)],
    )


async def cmd_startbot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Restart agent using persisted config — no extra args needed."""
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /startbot <agent_id>")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    try:
        result = await client.start_agent(agent_id)
        name = result.get("name", "?")
        await msg.reply_text(f"Agent {name} restarted — {result.get('status', '?')}")
    except Exception as e:
        await msg.reply_text(f"Error: {e}")


async def cmd_stopbot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /stopbot <agent_id>")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    try:
        await client.stop_agent(agent_id)
        await msg.reply_text(f"Agent {agent_id[:8]} stopped.")
    except Exception as e:
        await msg.reply_text(f"Error: {e}")


async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Show recent log entries with level and message."""
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /logs <agent_id>")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    try:
        logs = await client.get_logs(agent_id, limit=15)
        if not logs:
            await msg.reply_text("No logs.")
            return
        level_icons = {
            "action": "\U0001f3af", "sl_tp": "\U0001f6a8", "supervisor": "\U0001f9d1\u200d\U0001f4bb",
            "error": "\u274c", "warn": "\u26a0\ufe0f", "llm": "\U0001f916",
            "init": "\U0001f680", "start": "\u25b6\ufe0f", "stop": "\u23f9\ufe0f",
            "tick": "\U0001f4c9",
        }
        lines = [f"Last {len(logs)} log entries:\n"]
        for e in logs:
            lvl = e.get("level", "?")
            icon = level_icons.get(lvl, "\U0001f4dd")
            message = e.get("message", "")
            # truncate long messages for telegram
            if len(message) > 120:
                message = message[:117] + "..."
            lines.append(f"{icon} [{lvl}] {message}")
        await msg.reply_text("\n".join(lines))
    except Exception as e:
        await msg.reply_text(f"Error: {e}")


EDIT_FIELD_MAP = {
    "amount": "amount_usdt", "leverage": "leverage", "tp": "tp_pct",
    "sl": "sl_pct", "risk": "risk_profile", "supervisor": "supervisor_interval",
    "poll": "poll_seconds", "llm": "llm_provider", "name": "name",
}
NUMERIC_EDIT_FIELDS = {"amount_usdt", "leverage", "tp_pct", "sl_pct",
                       "supervisor_interval", "poll_seconds"}


async def cmd_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/edit <agent_id> <field> <value>"""
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if len(ctx.args) < 3:
        await msg.reply_text(
            "Usage: /edit <agent_id> <field> <value>\n\n"
            "Fields:\n"
            "  amount — capital in USDT (e.g. 500)\n"
            "  leverage — 1 to 125 (e.g. 10)\n"
            "  tp — take profit % as decimal (e.g. 0.05 = 5%)\n"
            "  sl — stop loss % as decimal (e.g. 0.02 = 2%)\n"
            "  risk — conservative | moderate | aggressive\n"
            "  supervisor — check interval 30-300 sec\n"
            "  poll — market poll interval >=0.5 sec\n"
            "  llm — provider name (e.g. anthropic)\n"
            "  name — agent display name\n\n"
            "Example: /edit abc123 amount 500"
        )
        return

    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return

    field = EDIT_FIELD_MAP.get(ctx.args[1].lower())
    if not field:
        await msg.reply_text(f"Unknown field: {ctx.args[1]}\nValid: {', '.join(EDIT_FIELD_MAP.keys())}")
        return

    value_str = ctx.args[2]
    try:
        if field in NUMERIC_EDIT_FIELDS:
            value = float(value_str) if "." in value_str else int(value_str)
        else:
            value = value_str
    except ValueError:
        await msg.reply_text(f"Invalid value for {field}: {value_str}")
        return

    try:
        result = await client.edit_agent(agent_id, **{field: value})
        status = result.get("status", "unknown")
        await msg.reply_text(f"Updated {field} -> {value}\nAgent: {result.get('name')} | {status}")
    except Exception as e:
        await msg.reply_text(f"Edit failed: {e}")


async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/leaderboard — show top 5 agents globally."""
    msg = _reply(update)
    hub = HubClient(base_url=HUB_URL)
    try:
        data = await hub.get_leaderboard(limit=5, sort_by="total_pnl")
        entries = data.get("leaderboard", [])
        if not entries:
            await msg.reply_text("No agents on the leaderboard yet.\nOpt in with: /optin <agent_id>")
            return

        medals = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}
        lines = ["\U0001f3c6 Artic Global Leaderboard\n"]
        for e in entries:
            medal = medals.get(e["rank"], f"#{e['rank']}")
            pnl = e["total_pnl_usdt"]
            pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            status = "\U0001f7e2" if e["is_running"] else "\u26aa"
            lines.append(
                f"{medal} {e['agent_name']} ({e['symbol']})\n"
                f"  {status} Owner: {e['owner']}\n"
                f"  Strategy: {e['top_strategy']}\n"
                f"  PnL: {pnl_str} | Win: {e['win_rate']*100:.0f}% | "
                f"Sharpe: {e['sharpe_ratio']:.2f}\n"
            )
        total = data.get("total_agents", 0)
        lines.append(f"\n{total} agents competing globally")
        await msg.reply_text("\n".join(lines))
    except Exception as e:
        await msg.reply_text(f"Failed: {e}")


async def cmd_optin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/optin <agent_id> [handle]"""
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /optin <agent_id> [handle]")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    handle = ctx.args[1] if len(ctx.args) > 1 else None
    try:
        result = await client.set_leaderboard_opt_in(agent_id, True, handle)
        await msg.reply_text(
            f"Agent joined leaderboard!\n"
            f"Display name: {result.get('handle', 'anonymized')}\n"
            "Check /leaderboard to see rankings"
        )
    except Exception as e:
        await msg.reply_text(f"Failed: {e}")


async def cmd_optout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/optout <agent_id>"""
    msg = _reply(update)
    client = _get_client(update.effective_chat.id)
    if not client:
        await msg.reply_text("Not logged in.")
        return
    if not ctx.args:
        await msg.reply_text("Usage: /optout <agent_id>")
        return
    agent_id = await _resolve_agent_id(client, ctx.args[0], msg)
    if not agent_id:
        return
    try:
        await client.set_leaderboard_opt_in(agent_id, False)
        await msg.reply_text("Agent removed from leaderboard")
    except Exception as e:
        await msg.reply_text(f"Failed: {e}")


def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("register", cmd_register))
    app.add_handler(CommandHandler("login", cmd_login))
    app.add_handler(CommandHandler("agents", cmd_agents))
    app.add_handler(CommandHandler("agent", cmd_agent))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("symbols", cmd_symbols))
    app.add_handler(_build_create_conversation())
    app.add_handler(CommandHandler("startbot", cmd_startbot))
    app.add_handler(CommandHandler("stopbot", cmd_stopbot))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("edit", cmd_edit))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(CommandHandler("optin", cmd_optin))
    app.add_handler(CommandHandler("optout", cmd_optout))

    print("Artic Telegram bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
