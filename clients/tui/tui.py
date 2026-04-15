"""
Bela TUI — manage multiple trading agents from the terminal.
Run: python tui.py
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Static, Input, Label, Button,
    ListView, ListItem, RichLog, Select, Switch, RadioSet, RadioButton,
)
from textual.screen import Screen
from textual.binding import Binding
from textual.reactive import reactive
from textual.theme import Theme
from textual import work
from rich.text import Text

from .hub_adapter import HubAdapter, AgentInfo
from .login_screen import LoginScreen, LOGIN_CSS

# ── Supported trading pairs (shown in token dropdown) ────────────────────────
SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT",
    "DOTUSDT", "LTCUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT",
    "ARBUSDT", "OPUSDT", "SUIUSDT", "APTUSDT", "PEPEUSDT",
    "RNDRUSDT", "INJUSDT", "TONUSDT", "POLUSDT",
]

# ── UI Color Constants ────────────────────────────────────────────────────────
# Edit the hex values below to customise every colour in the TUI.
#
#  Key           What it controls
#  ──────────────────────────────────────────────────────────────────────────
#  accent_1-6    theme accent slots (primary, secondary, accent, footer keys)
#  accent_mut    blurred/inactive borders, input background tint
#  accent_brt    hover states (scrollbar hover, button hover)
#  text_accent   banner text, header labels, shortcut bar, section titles,
#                input focus border, Launch button fill
#  border_card   round borders on detail-section cards and log display
#  border_panel  structural dividers: GlobalHeader bottom, agent-list right
#  border_form   round borders on Create Agent form sections
#  profit        positive PnL numbers
#  loss          negative PnL numbers, errors, stopped-agent dot
#  running_dot   running-agent status indicator  ●
#  warn          warning log messages
#  text          primary body text
#  text_muted    labels and dim secondary info
#  ──────────────────────────────────────────────────────────────────────────

COLORS = {
    "accent_1":    "#DA7756",
    "accent_2":    "#E4473B",
    "accent_3":    "#d000d0",
    "accent_4":    "#d0d000",
    "accent_5":    "#d00000",
    "accent_6":    "#0000d0",
    "accent_mut":  "#5A3020",
    "accent_brt":  "#F0A070",
    "text_accent":  "#DA7756",
    "border_card":  "#3A2A1A",
    "border_panel": "#5a5a5a",
    "border_form":  "#8a8a8a",
    "profit":      "#00d26a",
    "loss":        "#ff4444",
    "running_dot": "#DA7756",
    "warn":        "#ffff00",
    "text":        "#EEEEEE",
    "text_muted":  "#666666",
}


def _build_bela_theme() -> Theme:
    """Build the single BELA theme from the COLORS constants above."""
    c = COLORS
    return Theme(
        name="bela",
        primary=c["accent_1"],
        secondary=c["accent_2"],
        accent=c["accent_3"],
        foreground=c["text"],
        background="#000000",
        surface="#000000",
        panel="#0a0a0a",
        boost="#111111",
        warning=c["warn"],
        error=c["loss"],
        success=c["profit"],
        dark=True,
        variables={
            "$footer-background": "#000000",
            "$footer-foreground": c["accent_4"],
            "$footer-key-foreground": "#000000",
            "$footer-key-background": c["accent_5"],
            "$footer-description-foreground": c["accent_6"],
            "$footer-description-background": "#000000",
            "$footer-item-background": "#000000",
            "$border": c["text_accent"],
            "$border-blurred": c["accent_mut"],

            "$scrollbar": c["accent_1"],
            "$scrollbar-hover": c["accent_2"],
            "$scrollbar-active": c["accent_2"],
            "$scrollbar-background": "#0a0a0a",
            "$scrollbar-corner-color": "#000000",
            "$input-cursor-background": c["accent_1"],
            "$input-cursor-foreground": "#000000",
            "$input-selection-background": c["accent_mut"],
            "$block-cursor-foreground": "#000000",
            "$block-cursor-background": c["accent_1"],
            "$block-cursor-blurred-foreground": c["accent_1"],
            "$block-cursor-blurred-background": "#0a0a0a",
            "$text": c["text"],
            "$text-muted": c["text_muted"],
            "$text-disabled": "#333333",
            "$button-foreground": "#000000",
            "$button-color-foreground": "#000000",
        },
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEVEL_FILTERS = {
    "ALL": None,
    "INFO": {"init", "start", "action", "sl_tp", "stop"},
    "LLM": {"llm", "supervisor"},
    "ERROR": {"error", "warn"},
    "TICK": {"tick"},
}

LOG_COLORS = {
    "error": "red", "warn": "yellow", "llm": "cyan",
    "supervisor": "cyan", "tick": "dim white", "action": "green",
    "sl_tp": "magenta", "init": "blue", "start": "green", "stop": "red",
}

RISK_TAGS = {
    "conservative": ("[blue]\\[C][/blue]"),
    "moderate": ("[yellow]\\[M][/yellow]"),
    "aggressive": ("[red]\\[A][/red]"),
}

# ---------------------------------------------------------------------------
# ASCII Art
# ---------------------------------------------------------------------------

BELA_ASCII = (
    "██████╗ ███████╗██╗      █████╗ \n"
    "██╔══██╗██╔════╝██║     ██╔══██╗\n"
    "██████╔╝█████╗  ██║     ███████║\n"
    "██╔══██╗██╔══╝  ██║     ██╔══██╗\n"
    "██████╔╝███████╗███████╗██║  ██║\n"
    "╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝"
)

ARTIC_ASCII = (
    " █████╗ ██████╗  ██████╗████████╗██╗ ██████╗\n"
    "██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██║██╔════╝\n"
    "███████║██████╔╝██║        ██║   ██║██║     \n"
    "██╔══██║██╔══██╗██║        ██║   ██║██║     \n"
    "██║  ██║██║  ██║╚██████╗   ██║   ██║╚██████╗\n"
    "╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝"
)


# ═══════════════════════════════════════════════════════════════════════════
# Global Header  (shared across all screens)
# ═══════════════════════════════════════════════════════════════════════════

class GlobalHeader(Horizontal):
    """Persistent 1-row bar: current page (left) | agents + PnL (right)."""

    def compose(self) -> ComposeResult:
        yield Static("", id="gh-page")
        yield Static("", id="gh-stats")

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(2, self._refresh)

    def _refresh(self) -> None:
        app = self.app  # type: BelaTUI
        running = sum(1 for a in app.manager.agents.values() if a.alive)
        total = len(app.manager.agents)
        pnl = getattr(app, "total_pnl", 0.0)
        page = getattr(app, "current_page", "")
        pnl_c = COLORS["profit"] if pnl >= 0 else COLORS["loss"]
        ac = COLORS["accent_1"]
        self.query_one("#gh-page", Static).update(
            f" [{ac}]{page}[/{ac}]"
        )
        self.query_one("#gh-stats", Static).update(
            f"[dim]agents:[/dim] [{ac}]{running}[/{ac}]/{total}  "
            f"[dim]pnl:[/dim] [{pnl_c}]${pnl:+.2f}[/{pnl_c}] "
        )


# ═══════════════════════════════════════════════════════════════════════════
# Navigation Bar (bottom drop-up)
# ═══════════════════════════════════════════════════════════════════════════

class NavBar(Horizontal):
    """Bottom nav bar with drop-up page selector + shortcut hints."""

    NAV_OPTIONS = [
        ("Dashboard", "dashboard"),
        ("Create Agent", "create"),
        ("Logs", "logs"),
        ("ASCII Lab", "ascii_lab"),
        ("Leaderboard", "leaderboard"),
    ]

    def compose(self) -> ComposeResult:
        yield Select(
            [(label, val) for label, val in self.NAV_OPTIONS],
            prompt="Navigate",
            id="nav-select",
            allow_blank=True,
        )
        yield Static("", id="nav-shortcuts")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "nav-select" or event.value is Select.BLANK:
            return
        page = str(event.value)
        if page == "leaderboard":
            self.app.push_screen(LeaderboardScreen())
        else:
            self.app.switch_screen(page)
        self.query_one("#nav-select", Select).clear()


# ═══════════════════════════════════════════════════════════════════════════
# Dashboard Screen
# ═══════════════════════════════════════════════════════════════════════════

class AgentCard(Static):
    """Single agent row in the left panel list."""

    def __init__(self, agent_id: str, markup: str, **kw):
        super().__init__(markup, **kw)
        self.agent_id = agent_id


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("a", "create_agent", "Create"),
        Binding("s", "start_agent", "Start"),
        Binding("f", "start_all", "Start All"),
        Binding("d", "delete_agent", "Delete"),
        Binding("p", "stop_agent", "Stop"),
        Binding("c", "stop_all", "Stop All"),
        Binding("r", "refresh", "Refresh"),
        Binding("e", "edit_agent", "Edit"),
        Binding("b", "leaderboard", "Leaderboard"),
        Binding("o", "opt_in", "Opt-in"),
    ]

    selected_agent_id: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Static(ARTIC_ASCII, id="ascii-banner")
        yield GlobalHeader(id="global-header")
        with Horizontal(id="dashboard-body"):
            with Vertical(id="agent-list-panel"):
                yield ListView(id="agent-list")
            with Vertical(id="agent-detail-panel"):
                yield Static("", id="detail-header")
                with Horizontal(id="detail-grid-top"):
                    yield Static("", id="detail-overview", classes="detail-section")
                    yield Static("", id="detail-strategy", classes="detail-section")
                with Horizontal(id="detail-grid-bottom"):
                    yield Static("", id="detail-models", classes="detail-section")
                    yield Static("", id="detail-config", classes="detail-section")
        yield NavBar(id="nav-bar")

    async def on_mount(self) -> None:
        self.app.current_page = "Dashboard"
        self._latest_statuses: dict = {}
        self._update_shortcuts()
        await self.app.manager.refresh_agents()
        await self._refresh_list()
        self.set_interval(2, self._poll)

    def on_screen_resume(self) -> None:
        self.app.current_page = "Dashboard"
        self._update_shortcuts()
        self._poll()

    def _update_shortcuts(self) -> None:
        ac = COLORS["accent_1"]
        self.query_one("#nav-shortcuts", Static).update(
            f"[{ac}]a[/{ac}]:create [{ac}]s[/{ac}]:start "
            f"[{ac}]f[/{ac}]:all [{ac}]d[/{ac}]:del "
            f"[{ac}]p[/{ac}]:stop [{ac}]c[/{ac}]:stopall "
            f"[{ac}]r[/{ac}]:refresh [{ac}]e[/{ac}]:edit "
            f"[{ac}]b[/{ac}]:board [{ac}]o[/{ac}]:opt-in"
        )

    @work(exclusive=True)
    async def _poll(self) -> None:
        try:
            self._poll_count = getattr(self, "_poll_count", 0) + 1
            if self._poll_count % 5 == 0:
                await self.app.manager.refresh_agents()
            if self.app.manager.agents:
                self._latest_statuses = await self.app.manager.status_all()
            self.app.total_pnl = sum(
                (self._latest_statuses.get(aid) or {}).get("unrealized_pnl_usdt") or 0
                for aid in self.app.manager.agents
            )
            await self._refresh_list()
            self._update_detail()
        except Exception:
            pass

    # ── list ──────────────────────────────────────────────────────────

    async def _refresh_list(self):
        lv = self.query_one("#agent-list", ListView)
        old_idx = lv.index or 0
        await lv.clear()
        for aid, info in self.app.manager.agents.items():
            st = self._latest_statuses.get(aid)
            markup = self._render_card(info, st)
            item = ListItem(AgentCard(aid, markup), id=f"li-{aid}")
            if not info.alive:
                item.add_class("stopped-item")
            lv.append(item)
        if lv.children:
            lv.index = min(old_idx, len(lv.children) - 1)
            self._sync_selection()

    def _render_card(self, info: AgentInfo, st: dict | None) -> str:
        pnl_val = (st or {}).get("unrealized_pnl_usdt") or 0
        pnl_c = COLORS["profit"] if pnl_val >= 0 else COLORS["loss"]
        is_stale = (st or {}).get("error")
        if is_stale and info.alive:
            dot = f"[{COLORS['accent_1']}]\u26a0[/{COLORS['accent_1']}]"
        elif info.alive:
            dot = f"[{COLORS['running_dot']}]\u25cf[/{COLORS['running_dot']}]"
        else:
            dot = f"[{COLORS['loss']}]\u25cb[/{COLORS['loss']}]"
        tag = RISK_TAGS.get(info.risk_profile, "[dim]\\[?][/dim]")
        stale_tag = " [dim](stale)[/dim]" if is_stale else ""
        return (
            f"{dot} {info.name} {tag}  [{pnl_c}]{pnl_val:+.2f}[/{pnl_c}]{stale_tag}\n"
            f"  [dim]{info.agent_id} : {info.port}[/dim]"
        )

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        self._sync_selection()

    def _sync_selection(self):
        lv = self.query_one("#agent-list", ListView)
        if lv.highlighted_child is not None:
            card = lv.highlighted_child.query_one(AgentCard)
            if card:
                self.selected_agent_id = card.agent_id
                return
        self.selected_agent_id = None

    # ── detail panel ──────────────────────────────────────────────────

    def watch_selected_agent_id(self, old: str | None, new: str | None) -> None:
        self._update_detail()

    def _update_detail(self):
        aid = self.selected_agent_id
        info = self.app.manager.agents.get(aid) if aid else None
        st = self._latest_statuses.get(aid) if aid else None

        header = self.query_one("#detail-header", Static)
        overview = self.query_one("#detail-overview", Static)
        strategy = self.query_one("#detail-strategy", Static)
        models = self.query_one("#detail-models", Static)
        config = self.query_one("#detail-config", Static)

        if not info:
            header.update("[dim]No agent selected[/dim]")
            for w in (overview, strategy, models, config):
                w.update("")
            return

        ac = COLORS["accent_1"]
        pnl_val = (st or {}).get("unrealized_pnl_usdt") or 0
        pnl_c = COLORS["profit"] if pnl_val >= 0 else COLORS["loss"]
        header.update(
            f"[bold {ac}]{info.name}[/bold {ac}]                       "
            f"[{pnl_c}]{pnl_val:+.2f}[/{pnl_c}]\n"
            f"[dim]{info.agent_id} : {info.port}[/dim]"
        )

        is_stale = (st or {}).get("error")
        if is_stale and info.alive:
            status_txt = f"[{COLORS['accent_1']}]Unreachable[/{COLORS['accent_1']}] [dim](stale data)[/dim]"
        elif info.alive:
            status_txt = f"[{ac}]Running[/{ac}]"
        else:
            status_txt = f"[{COLORS['loss']}]Stopped[/{COLORS['loss']}]"
        side = (st or {}).get("side", "FLAT")
        entry = f"${st['entry_price']:,.2f}" if st and st.get("entry_price") else f"{info.amount_usdt} USDT"
        price = f"${st['last_price']:,.2f}" if st and st.get("last_price") else "—"
        act = (st or {}).get("last_action") or "[dim]HOLD[/dim]"
        reason = (st or {}).get("last_reason") or "[dim]Waiting for signal...[/dim]"
        strat = (st or {}).get("active_strategy") or "[dim]Initializing...[/dim]"
        tp_str = f"{info.tp_pct*100:.1f}%" if info.tp_pct else "Auto"
        sl_str = f"{info.sl_pct*100:.1f}%" if info.sl_pct else "Auto"

        overview.update(
            f"[bold {ac}]Overview[/bold {ac}]\n"
            f"[dim]Status:[/dim]    {status_txt}\n"
            f"[dim]Token:[/dim]     {info.symbol}\n"
            f"[dim]Amount:[/dim]    {info.amount_usdt} USDT\n"
            f"[dim]Price:[/dim]     {price}\n"
            f"[dim]Entry:[/dim]     {entry}\n"
            f"[dim]Leverage:[/dim]  {info.leverage}x\n"
            f"[dim]Side:[/dim]      {side}\n"
            f"[dim]Risk:[/dim]      {info.risk_profile.title()}"
        )

        strategy.update(
            f"[bold {ac}]Strategy[/bold {ac}]\n"
            f"[dim]Active:[/dim]      {strat}\n"
            f"[dim]Last Action:[/dim] {act}\n"
            f"[dim]Last Reason:[/dim] {reason}\n"
            f"[dim]Timeframe:[/dim]   {info.timeframe}"
        )

        models.update(
            f"[bold {ac}]Models[/bold {ac}]\n"
            f"[dim]LLM Provider:[/dim]  {info.llm_provider or 'auto'}\n"
            f"[dim]Supervisor:[/dim]    every {info.supervisor_interval}s"
        )

        config.update(
            f"[bold {ac}]Config[/bold {ac}]\n"
            f"[dim]TP/SL Mode:[/dim]   {info.tp_sl_mode}\n"
            f"[dim]Take Profit:[/dim]  {tp_str}\n"
            f"[dim]Stop Loss:[/dim]    {sl_str}\n"
            f"[dim]Poll:[/dim]         {info.poll_seconds}s\n"
            f"[dim]Live Mode:[/dim]    {'Yes' if info.live_mode else 'No (Paper)'}"
        )

    # ── actions ───────────────────────────────────────────────────────

    def action_create_agent(self):
        self.app.switch_screen("create")

    def action_start_agent(self):
        if self.selected_agent_id:
            self._do_start(self.selected_agent_id)

    @work(exclusive=False)
    async def _do_start(self, agent_id: str) -> None:
        info = self.app.manager.agents.get(agent_id)
        if not info or info.alive:
            return
        self.notify(f"Starting {info.name}...")
        try:
            await self.app.manager.start_agent(agent_id)
            self.notify(f"{info.name} started")
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")

    def action_start_all(self):
        self._do_start_all()

    @work(exclusive=False)
    async def _do_start_all(self) -> None:
        import asyncio
        stopped = [a for a in self.app.manager.agents.values() if not a.alive]
        if not stopped:
            self.notify("No stopped agents")
            return
        self.notify(f"Starting {len(stopped)} agents...")
        await asyncio.gather(
            *(self.app.manager.start_agent(info.agent_id) for info in stopped),
            return_exceptions=True,
        )
        self.notify("Done")

    def action_stop_agent(self):
        if self.selected_agent_id:
            self._do_stop(self.selected_agent_id)

    @work(exclusive=False)
    async def _do_stop(self, agent_id: str) -> None:
        info = self.app.manager.agents.get(agent_id)
        if not info or not info.alive:
            return
        self.notify(f"Stopping {info.name}...")
        await self.app.manager.stop(agent_id)
        self.notify(f"{info.name} stopped")

    def action_delete_agent(self):
        if self.selected_agent_id:
            self._do_delete(self.selected_agent_id)

    @work(exclusive=False)
    async def _do_delete(self, agent_id: str) -> None:
        info = self.app.manager.agents.get(agent_id)
        name = info.name if info else agent_id
        self.notify(f"Deleting {name}...")
        try:
            await self.app.manager.delete(agent_id)
            self.selected_agent_id = None
            await self._refresh_list()
            self.notify(f"{name} deleted")
        except Exception as e:
            self.notify(f"Delete failed: {e}", severity="error")

    def action_stop_all(self):
        self._do_stop_all()

    @work(exclusive=False)
    async def _do_stop_all(self) -> None:
        self.notify("Stopping all agents...")
        await self.app.manager.stop_all()
        self.notify("All agents stopped")

    def action_refresh(self):
        self._poll()

    def action_edit_agent(self):
        if self.selected_agent_id:
            info = self.app.manager.agents.get(self.selected_agent_id)
            if info:
                self.app.push_screen(EditAgentScreen(info))

    def action_leaderboard(self):
        self.app.push_screen(LeaderboardScreen())

    def action_opt_in(self):
        if self.selected_agent_id:
            self._do_opt_in(self.selected_agent_id)

    @work(exclusive=False)
    async def _do_opt_in(self, agent_id: str) -> None:
        info = self.app.manager.agents.get(agent_id)
        if not info:
            return
        new_state = not info.leaderboard_opt_in
        try:
            await self.app.manager.set_leaderboard_opt_in(agent_id, new_state)
            info.leaderboard_opt_in = new_state
            action = "joined" if new_state else "left"
            self.notify(f"Agent {action} leaderboard")
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")


# ═══════════════════════════════════════════════════════════════════════════
# Edit Agent Screen
# ═══════════════════════════════════════════════════════════════════════════


class EditAgentScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Cancel"),
    ]

    def __init__(self, agent_info: "AgentInfo"):
        super().__init__()
        self._info = agent_info

    def compose(self) -> ComposeResult:
        yield Static(ARTIC_ASCII, id="ascii-banner")
        yield GlobalHeader(id="global-header")
        with VerticalScroll(id="create-scroll"):
            yield Label(f"Edit Agent: {self._info.name}", id="form-title")

            with Vertical(classes="form-section"):
                yield Label("Config", classes="section-label")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Agent Name")
                        yield Input(value=self._info.name, id="edit-name")
                    with Vertical(classes="form-col"):
                        yield Label("Amount (USDT)")
                        yield Input(value=str(self._info.amount_usdt), id="edit-amount", type="number")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Leverage")
                        yield Input(value=str(self._info.leverage), id="edit-leverage", type="integer")
                    with Vertical(classes="form-col"):
                        yield Label("Risk Profile")
                        yield Input(value=self._info.risk_profile, id="edit-risk")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Take Profit %")
                        yield Input(value=str(self._info.tp_pct or ""), id="edit-tp", placeholder="auto")
                    with Vertical(classes="form-col"):
                        yield Label("Stop Loss %")
                        yield Input(value=str(self._info.sl_pct or ""), id="edit-sl", placeholder="auto")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Supervisor Interval (s)")
                        yield Input(value=str(self._info.supervisor_interval), id="edit-supervisor", type="number")
                    with Vertical(classes="form-col"):
                        yield Label("Poll Interval (s)")
                        yield Input(value=str(self._info.poll_seconds), id="edit-poll", type="number")

            if self._info.alive:
                with Vertical(classes="form-section"):
                    yield Label(
                        "Agent is running. TP/SL/amount apply immediately. "
                        "Leverage/LLM changes trigger restart.",
                        classes="section-label",
                    )

            with Horizontal(id="form-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-launch")

    def on_mount(self) -> None:
        self.app.current_page = "Edit Agent"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.action_go_back()
        elif event.button.id == "btn-launch":
            self._submit()

    def _submit(self):
        updates = {}
        name = self.query_one("#edit-name", Input).value.strip()
        if name and name != self._info.name:
            updates["name"] = name

        try:
            amount = float(self.query_one("#edit-amount", Input).value.strip() or "0")
            if amount and amount != self._info.amount_usdt:
                updates["amount_usdt"] = amount
        except ValueError:
            pass

        try:
            lev = int(self.query_one("#edit-leverage", Input).value.strip() or "0")
            if lev and lev != self._info.leverage:
                updates["leverage"] = lev
        except ValueError:
            pass

        risk = self.query_one("#edit-risk", Input).value.strip()
        if risk and risk != self._info.risk_profile:
            updates["risk_profile"] = risk

        tp_str = self.query_one("#edit-tp", Input).value.strip()
        try:
            tp_val = float(tp_str) if tp_str else None
        except ValueError:
            tp_val = self._info.tp_pct
        if tp_val != self._info.tp_pct:
            updates["tp_pct"] = tp_val

        sl_str = self.query_one("#edit-sl", Input).value.strip()
        try:
            sl_val = float(sl_str) if sl_str else None
        except ValueError:
            sl_val = self._info.sl_pct
        if sl_val != self._info.sl_pct:
            updates["sl_pct"] = sl_val

        try:
            sup = float(self.query_one("#edit-supervisor", Input).value.strip() or "0")
            if sup and sup != self._info.supervisor_interval:
                updates["supervisor_interval"] = sup
        except ValueError:
            pass

        try:
            poll = float(self.query_one("#edit-poll", Input).value.strip() or "0")
            if poll and poll != self._info.poll_seconds:
                updates["poll_seconds"] = poll
        except ValueError:
            pass

        if not updates:
            self.notify("No changes", severity="warning")
            return

        self._do_save(updates)

    @work(exclusive=False)
    async def _do_save(self, updates: dict) -> None:
        try:
            await self.app.manager.edit_agent(self._info.agent_id, **updates)
            self.notify("Agent updated")
            self.app.pop_screen()
        except Exception as e:
            self.notify(f"Update failed: {e}", severity="error")

    def action_go_back(self):
        self.app.pop_screen()


# ═══════════════════════════════════════════════════════════════════════════
# Leaderboard Screen
# ═══════════════════════════════════════════════════════════════════════════


class LeaderboardScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(ARTIC_ASCII, id="ascii-banner")
        yield GlobalHeader(id="global-header")
        with Vertical(id="ascii-lab-body"):
            yield Label("Global Leaderboard", id="lab-title")
            yield Static("Loading...", id="leaderboard-content")
            yield Static("", id="lab-status")

    def on_mount(self) -> None:
        self.app.current_page = "Leaderboard"
        self._load()

    def on_screen_resume(self) -> None:
        self.app.current_page = "Leaderboard"

    def action_refresh(self):
        self._load()

    @work(exclusive=True)
    async def _load(self) -> None:
        try:
            data = await self.app.manager.get_leaderboard(limit=20)
            entries = data.get("leaderboard", [])
            if not entries:
                self.query_one("#leaderboard-content", Static).update(
                    "[dim]No agents on the leaderboard yet.[/dim]"
                )
                return

            ac = COLORS["accent_1"]
            lines = []
            medals = {1: "1st", 2: "2nd", 3: "3rd"}
            header = (
                f"{'RANK':<6} {'AGENT':<16} {'SYMBOL':<10} {'OWNER':<14} "
                f"{'STRATEGY':<16} {'TRADES':<7} {'PNL':>10} {'WIN%':>7} {'SHARPE':>7}"
            )
            lines.append(f"[{ac}]{header}[/{ac}]")
            lines.append("[dim]" + "-" * 95 + "[/dim]")

            for e in entries:
                pnl = e["total_pnl_usdt"]
                pnl_c = COLORS["profit"] if pnl >= 0 else COLORS["loss"]
                pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
                rank_str = medals.get(e["rank"], str(e["rank"]))
                lines.append(
                    f"{rank_str:<6} {e['agent_name'][:15]:<16} {e['symbol']:<10} "
                    f"{e['owner'][:13]:<14} {e['top_strategy'][:15]:<16} "
                    f"{e['total_trades']:<7} [{pnl_c}]{pnl_str:>10}[/{pnl_c}] "
                    f"{e['win_rate']*100:>6.1f}% {e['sharpe_ratio']:>7.2f}"
                )

            self.query_one("#leaderboard-content", Static).update("\n".join(lines))
            total = data.get("total_agents", 0)
            self.query_one("#lab-status", Static).update(
                f"[dim]{total} agents competing globally[/dim]"
            )
        except Exception as e:
            self.query_one("#leaderboard-content", Static).update(f"[red]Error: {e}[/red]")

    def action_go_back(self):
        self.app.pop_screen()


# ═══════════════════════════════════════════════════════════════════════════
# Create Agent Screen  (grid layout)
# ═══════════════════════════════════════════════════════════════════════════

class CreateAgentScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(ARTIC_ASCII, id="ascii-banner")
        yield GlobalHeader(id="global-header")
        with VerticalScroll(id="create-scroll"):
            yield Label("Create New Agent", id="form-title")

            # ── Identity ─────────────────────────────────────────────
            with Vertical(classes="form-section"):
                yield Label("Identity", classes="section-label")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Agent Name")
                        yield Input(placeholder="My BTC Bot", id="inp-name")
                    with Vertical(classes="form-col"):
                        yield Label("Token Symbol")
                        yield Select(
                            [(pair, pair) for pair in sorted(set(SUPPORTED_SYMBOLS))],
                            prompt="Select token",
                            id="inp-symbol",
                        )

            # ── Trading Config ────────────────────────────────────────
            with Vertical(classes="form-section"):
                yield Label("Trading Config", classes="section-label")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Amount (USDT)")
                        yield Input(placeholder="1000", id="inp-amount", type="number")
                    with Vertical(classes="form-col"):
                        yield Label("Leverage (1-125)")
                        yield Input(placeholder="5", id="inp-leverage", type="integer")
                    with Vertical(classes="form-col"):
                        yield Label("Timeframe")
                        yield Input(placeholder="15m", id="inp-timeframe")
                    with Vertical(classes="form-col"):
                        yield Label("Poll Interval (s)")
                        yield Input(placeholder="1.0", id="inp-poll", type="number")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Risk Profile")
                        yield RadioSet(
                            RadioButton("Conservative", id="risk-conservative"),
                            RadioButton("Moderate", value=True, id="risk-moderate"),
                            RadioButton("Aggressive", id="risk-aggressive"),
                            id="risk-radio",
                        )

            # ── TP/SL  +  Execution/Supervisor  (side by side) ───────
            with Horizontal(classes="form-row"):
                with Vertical(classes="form-section"):
                    yield Label("TP / SL", classes="section-label")
                    yield RadioSet(
                        RadioButton("Fixed", value=True, id="tpsl-fixed"),
                        RadioButton("Dynamic (ATR)", id="tpsl-dynamic"),
                        id="tpsl-radio",
                    )
                    with Horizontal(classes="form-row"):
                        with Vertical(classes="form-col"):
                            yield Label("Take Profit %")
                            yield Input(placeholder="optional", id="inp-tp", type="number")
                        with Vertical(classes="form-col"):
                            yield Label("Stop Loss %")
                            yield Input(placeholder="optional", id="inp-sl", type="number")
                with Vertical(classes="form-section"):
                    yield Label("Execution + Supervisor", classes="section-label")
                    yield RadioSet(
                        RadioButton("Paper Trading", value=True, id="live-paper"),
                        RadioButton("Live (Pancake Perps)", id="live-real"),
                        id="live-radio",
                    )
                    with Horizontal(classes="form-row"):
                        with Vertical(classes="form-col"):
                            yield Label("Supervisor Interval (30-300s)")
                            yield Input(placeholder="60", id="inp-supervisor", type="number")

            # ── API Keys ──────────────────────────────────────────────
            with Vertical(classes="form-section"):
                yield Label("API Keys", classes="section-label")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Exchange API Key")
                        yield Input(placeholder="", id="inp-exkey")
                    with Vertical(classes="form-col"):
                        yield Label("Exchange Secret")
                        yield Input(placeholder="", id="inp-exsecret")
                    with Vertical(classes="form-col"):
                        yield Label("LLM API Key")
                        yield Input(placeholder="", id="inp-llmkey")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("LLM Provider")
                        yield RadioSet(
                            RadioButton("OpenAI", id="llm-openai"),
                            RadioButton("Anthropic", id="llm-anthropic"),
                            RadioButton("Gemini", value=True, id="llm-gemini"),
                            RadioButton("DeepSeek", id="llm-deepseek"),
                            id="llm-radio",
                        )

            # ── Buttons ───────────────────────────────────────────────
            with Horizontal(id="form-buttons"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Launch", variant="primary", id="btn-launch")
        yield NavBar(id="nav-bar")

    def on_mount(self) -> None:
        self.app.current_page = "Create Agent"
        ac = COLORS["accent_1"]
        self.query_one("#nav-shortcuts", Static).update(
            f"[{ac}]esc[/{ac}]:cancel"
        )

    def on_screen_resume(self) -> None:
        self.app.current_page = "Create Agent"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.action_go_back()
        elif event.button.id == "btn-launch":
            self._submit()

    def _get_radio_value(self, radio_id: str, mapping: dict) -> str:
        rs = self.query_one(f"#{radio_id}", RadioSet)
        if rs.pressed_button:
            return mapping.get(rs.pressed_button.id, list(mapping.values())[0])
        return list(mapping.values())[0]

    def _submit(self):
        symbol_val = self.query_one("#inp-symbol", Select).value
        if symbol_val is Select.BLANK:
            self.notify("Symbol is required", severity="error")
            return
        symbol = str(symbol_val)

        name = self.query_one("#inp-name", Input).value.strip() or f"{symbol} Agent"
        amount_str = self.query_one("#inp-amount", Input).value.strip() or "1000"
        leverage_str = self.query_one("#inp-leverage", Input).value.strip() or "5"
        timeframe = self.query_one("#inp-timeframe", Input).value.strip() or "15m"
        poll_str = self.query_one("#inp-poll", Input).value.strip() or "1.0"
        tp_str = self.query_one("#inp-tp", Input).value.strip()
        sl_str = self.query_one("#inp-sl", Input).value.strip()
        supervisor_str = self.query_one("#inp-supervisor", Input).value.strip() or "60"

        risk = self._get_radio_value("risk-radio", {
            "risk-conservative": "conservative",
            "risk-moderate": "moderate",
            "risk-aggressive": "aggressive",
        })
        tp_sl_mode = self._get_radio_value("tpsl-radio", {
            "tpsl-fixed": "fixed",
            "tpsl-dynamic": "dynamic",
        })
        live_mode = self._get_radio_value("live-radio", {
            "live-paper": "false",
            "live-real": "true",
        }) == "true"
        llm_provider = self._get_radio_value("llm-radio", {
            "llm-openai": "openai",
            "llm-anthropic": "anthropic",
            "llm-gemini": "gemini",
            "llm-deepseek": "deepseek",
        })

        exchange_key = self.query_one("#inp-exkey", Input).value.strip()
        exchange_secret = self.query_one("#inp-exsecret", Input).value.strip()
        llm_key = self.query_one("#inp-llmkey", Input).value.strip()

        try:
            amount = float(amount_str)
            leverage = int(leverage_str)
            poll = float(poll_str)
            supervisor = float(supervisor_str)
            tp_pct = float(tp_str) / 100 if tp_str else None
            sl_pct = float(sl_str) / 100 if sl_str else None
        except ValueError:
            self.notify("Invalid number in form", severity="error")
            return

        self._do_launch(
            symbol=symbol, name=name, amount_usdt=amount, leverage=leverage,
            risk_profile=risk, timeframe=timeframe, poll_seconds=poll,
            tp_pct=tp_pct, sl_pct=sl_pct, tp_sl_mode=tp_sl_mode,
            live_mode=live_mode, supervisor_interval=supervisor,
            llm_provider=llm_provider, exchange_api_key=exchange_key,
            exchange_secret=exchange_secret, llm_api_key=llm_key,
        )

    @work(exclusive=False)
    async def _do_launch(self, **kwargs) -> None:
        self.notify(f"Launching {kwargs['symbol']} agent...")
        try:
            info = await self.app.manager.launch(**kwargs)
            self.notify(f"{info.name} live on port {info.port}")
            self.app.switch_screen("dashboard")
        except Exception as e:
            self.notify(f"Failed: {e}", severity="error")

    def action_go_back(self):
        self.app.switch_screen("dashboard")


# ═══════════════════════════════════════════════════════════════════════════
# Log Viewer Screen
# ═══════════════════════════════════════════════════════════════════════════

class LogViewerScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(ARTIC_ASCII, id="ascii-banner")
        yield GlobalHeader(id="global-header")
        with Vertical(id="log-header"):
            with Horizontal(id="log-controls"):
                yield Select(
                    [("Select agent", "")],
                    id="log-agent-select",
                    prompt="Agent",
                )
                yield Select(
                    [(level, level) for level in LEVEL_FILTERS],
                    value="ALL",
                    id="log-level-select",
                    prompt="Level",
                )
                yield Input(placeholder="Search...", id="log-search")
            with Horizontal(id="log-autoscroll-row"):
                yield Label("Auto-scroll:")
                yield Switch(value=True, id="log-autoscroll")
        yield RichLog(id="log-display", highlight=True, markup=True)
        yield NavBar(id="nav-bar")

    def on_mount(self) -> None:
        self.app.current_page = "Log Viewer"
        self._last_log_count = 0
        self._all_logs: list[dict] = []
        self._displayed_count = 0
        self._mounted = False
        self._update_agent_options()
        self.set_interval(2, self._poll_logs)
        self._mounted = True

    def on_screen_resume(self) -> None:
        self.app.current_page = "Log Viewer"
        self._update_agent_options()

    def _update_agent_options(self):
        agents = self.app.manager.agents
        options = [(info.name, aid) for aid, info in agents.items() if info.alive]
        sel = self.query_one("#log-agent-select", Select)
        sel.set_options(options if options else [("No agents", "")])
        if options and sel.value == Select.BLANK:
            sel.value = options[0][1]

    @work(exclusive=True)
    async def _poll_logs(self) -> None:
        sel = self.query_one("#log-agent-select", Select)
        agent_id = sel.value
        if not agent_id or agent_id == Select.BLANK or agent_id not in self.app.manager.agents:
            return
        data = await self.app.manager.logs(str(agent_id))
        if not data:
            return
        logs = data.get("logs", [])
        if len(logs) != len(self._all_logs):
            new_entries = logs[len(self._all_logs):]
            self._all_logs = logs
            self._append_filtered(new_entries)

    def _append_filtered(self, entries: list[dict]):
        level_sel = self.query_one("#log-level-select", Select)
        level_val = str(level_sel.value) if level_sel.value != Select.BLANK else "ALL"
        allowed = LEVEL_FILTERS.get(level_val)
        search = self.query_one("#log-search", Input).value.strip().lower()

        log_widget = self.query_one("#log-display", RichLog)
        count = 0
        for entry in entries:
            lvl = entry.get("level", "")
            msg = entry.get("message", "")
            if allowed and lvl not in allowed:
                continue
            if search and search not in msg.lower():
                continue
            ts = entry.get("ts", "")
            if "T" in ts:
                ts = ts.split("T")[1].split(".")[0]
            color = LOG_COLORS.get(lvl, "white")
            log_widget.write(Text.from_markup(
                f"[dim]{ts}[/dim]  [{color}]{lvl:<12}[/{color}] {msg}"
            ))
            count += 1

        auto = self.query_one("#log-autoscroll", Switch).value
        if auto:
            log_widget.scroll_end(animate=False)

        self._displayed_count += count
        ac = COLORS["accent_1"]
        self.query_one("#nav-shortcuts", Static).update(
            f"Entries: {self._displayed_count}  [{ac}]esc[/{ac}]:back"
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        if not getattr(self, "_mounted", False):
            return
        if event.select.id == "log-agent-select":
            self._all_logs = []
            self._last_log_count = 0
            self._displayed_count = 0
            self.query_one("#log-display", RichLog).clear()
        elif event.select.id == "log-level-select":
            self._rerender_logs()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "log-search":
            self._rerender_logs()

    def _rerender_logs(self):
        self.query_one("#log-display", RichLog).clear()
        self._displayed_count = 0
        self._append_filtered(self._all_logs)

    def action_go_back(self):
        self.app.switch_screen("dashboard")


# ═══════════════════════════════════════════════════════════════════════════
# ASCII Art Lab Screen — 3D Rotating $ Sign
# ═══════════════════════════════════════════════════════════════════════════

import math

_GRADIENT = " .,:;+*#%@"
_GLEN = len(_GRADIENT) - 1

# ── Dollar sign bitmap (each '#' = solid) ──
_DOLLAR_SHAPE = [
    "       ##       ",
    "     ######     ",
    "   ####  ####   ",
    "  ####    ####  ",
    "  ####    ####  ",
    "  ####     #    ",
    "  #####         ",
    "   ######       ",
    "    #######     ",
    "      #######   ",
    "        #####   ",
    "    #     ####  ",
    "  ####    ####  ",
    "  ####    ####  ",
    "   ####  ####   ",
    "     ######     ",
    "       ##       ",
]
_SH = len(_DOLLAR_SHAPE)
_SW = max(len(r) for r in _DOLLAR_SHAPE)


def _bmp_solid(bx: float, by: float) -> bool:
    ix, iy = int(bx), int(by)
    if 0 <= iy < _SH and 0 <= ix < len(_DOLLAR_SHAPE[iy]):
        return _DOLLAR_SHAPE[iy][ix] == "#"
    return False


def _dollar_frame(angle_y: float, width: int = 60, height: int = 30) -> str:
    """Render one frame of a 3D extruded '$' sign rotating around Y axis."""
    ca, sa = math.cos(angle_y), math.sin(angle_y)
    depth = 4.0          # extrusion thickness in bitmap units
    hd = depth / 2.0
    aspect = 2.2         # terminal char height:width ratio
    scale = _SH / (height * 0.85)
    hsw = _SW * 0.5

    # Light direction (normalised) — upper-right-front
    lx, lz = 0.45, 0.78
    ln = math.sqrt(lx * lx + lz * lz)
    lx, lz = lx / ln, lz / ln

    # Pre-compute face lighting:
    #   Front face object-normal (0,0,1) in screen space → (sa, 0, ca)
    #   Side  face object-normal (±1,0,0) in screen space → (±ca, 0, ∓sa)
    front_bright = max(0.0, sa * lx + ca * lz) * 0.85 + 0.12
    back_bright = max(0.0, -sa * lx - ca * lz) * 0.55 + 0.08
    side_r_bright = max(0.0, ca * lx - sa * lz) * 0.7 + 0.10   # right-facing edge
    side_l_bright = max(0.0, -ca * lx + sa * lz) * 0.7 + 0.10  # left-facing edge

    lines: list[str] = []
    n_steps = 28  # ray-march steps

    for row in range(height):
        buf: list[str] = []
        by = (row - height * 0.5) * scale + _SH * 0.5

        for col in range(width):
            sx = (col - width * 0.5) * scale / aspect

            # Solve t-range from depth constraint:
            #   obj_z = -sx·sa + t·ca  must be in [-hd, hd]
            if abs(ca) > 1e-3:
                t0 = (-hd + sx * sa) / ca
                t1 = (hd + sx * sa) / ca
                if t0 > t1:
                    t0, t1 = t1, t0
            elif abs(sx * sa) <= hd:
                t0, t1 = -hsw, hsw
            else:
                buf.append(" ")
                continue

            # Ray-march to find first solid voxel
            ch = " "
            dt = (t1 - t0) / n_steps
            prev_solid = False
            for i in range(n_steps + 1):
                t = t0 + dt * i
                bx = sx * ca + t * sa + hsw
                solid = _bmp_solid(bx, by)

                if solid and not prev_solid:
                    # Determine which face we entered through
                    obj_z = -sx * sa + t * ca
                    at_z_face = (i == 0) or (abs(obj_z) > hd * 0.80)

                    if at_z_face:
                        bright = front_bright if obj_z > 0 else back_bright
                    else:
                        # Side edge: figure out left vs right normal
                        if _bmp_solid(bx + 0.6, by):
                            bright = side_l_bright  # entered from left
                        elif _bmp_solid(bx - 0.6, by):
                            bright = side_r_bright  # entered from right
                        else:
                            bright = (side_l_bright + side_r_bright) * 0.5

                    # Top/bottom edge darkening
                    if not _bmp_solid(bx, by - 0.8) or not _bmp_solid(bx, by + 0.8):
                        bright *= 0.85

                    idx = max(0, min(_GLEN, int(bright * _GLEN)))
                    ch = _GRADIENT[idx]
                    break

                prev_solid = solid

            buf.append(ch)
        lines.append("".join(buf))

    return "\n".join(lines)


class AsciiLabScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Static(ARTIC_ASCII, id="ascii-banner")
        yield GlobalHeader(id="global-header")
        with Vertical(id="ascii-lab-body"):
            yield Label("ASCII Art Lab", id="lab-title")
            yield Static("", id="ascii-frame")
        yield NavBar(id="nav-bar")

    def on_mount(self) -> None:
        self.app.current_page = "ASCII Lab"
        self._angle = 0.0
        self._frame_num = 0
        self._render_frame()
        self.set_interval(0.10, self._next_frame)

    def on_screen_resume(self) -> None:
        self.app.current_page = "ASCII Lab"

    def _next_frame(self) -> None:
        self._angle += 0.16
        self._frame_num += 1
        self._render_frame()

    def _render_frame(self) -> None:
        ac = COLORS["accent_1"]
        frame = _dollar_frame(self._angle, width=30, height=15)
        self.query_one("#ascii-frame", Static).update(f"[{ac}]{frame}[/{ac}]")
        self.query_one("#nav-shortcuts", Static).update(
            f"[{COLORS['text_muted']}]frame {self._frame_num}[/{COLORS['text_muted']}]  "
            f"[{ac}]esc[/{ac}]:back"
        )

    def action_go_back(self) -> None:
        self.app.switch_screen("dashboard")


# ═══════════════════════════════════════════════════════════════════════════
# Main App
# ═══════════════════════════════════════════════════════════════════════════

def _make_css(template: str) -> str:
    """Substitute custom color placeholders that Textual's theme vars don't support."""
    return (
        template
        .replace("$border-card",  COLORS["border_card"])
        .replace("$border-panel", COLORS["border_panel"])
        .replace("$border-form",  COLORS["border_form"])
    )


class BelaTUI(App):
    CSS = _make_css(LOGIN_CSS + """
    /* ── Global ── */
    Screen {
        background: #000000;
    }

    /* ── ASCII Banner ── */
    #ascii-banner {
        dock: top;
        height: 8;
        background: #000000;
        color: $border;
        padding: 1 2 0 2;
        text-align: center;
        border-bottom: solid $border-blurred;
    }

    /* ── Global Header ── */
    GlobalHeader {
        dock: top;
        height: 1;
        background: #0a0a0a;
        border-bottom: solid $border-panel;
    }
    #gh-page {
        width: 1fr;
        color: $text;
        content-align: left middle;
        padding: 0 1;
    }
    #gh-stats {
        width: auto;
        color: $text;
        text-align: right;
        padding: 0 1;
    }

    /* ── Dashboard ── */
    #dashboard-body {
        height: 1fr;
    }
    #agent-list-panel {
        width: 42;
        min-width: 30;
        border-right: solid $border-panel;
        background: #000000;
    }
    #agent-list-panel ListView {
        height: 1fr;
        background: #000000;
    }
    #agent-list-panel ListItem {
        height: 3;
        padding: 0 1;
        background: #000000;
        color: #EEEEEE;
    }
    #agent-list-panel ListItem:hover {
        background: $boost;
    }
    .stopped-item {
        opacity: 0.4;
    }
    #agent-detail-panel {
        width: 1fr;
        padding: 1 2;
        background: #000000;
    }
    #detail-header {
        height: auto;
        margin-bottom: 1;
        color: $border;
        text-style: bold;
    }
    #detail-grid-top, #detail-grid-bottom {
        height: 1fr;
    }
    .detail-section {
        width: 1fr;
        margin: 0 1 1 0;
        border: round $border-card;
        padding: 1 2;
        height: 1fr;
        background: #050505;
        color: #EEEEEE;
    }
    NavBar {
        dock: bottom;
        height: 3;
        background: #0a0a0a;
        border-top: solid $border-blurred;
        padding: 0 1;
    }
    NavBar #nav-select {
        width: 25;
    }
    NavBar #nav-shortcuts {
        width: 1fr;
        content-align: right middle;
        color: $border;
    }

    /* ── Create Agent Form ── */
    #create-scroll {
        height: 1fr;
        padding: 1 3;
        background: #000000;
    }
    #form-title {
        text-align: center;
        margin-bottom: 1;
        color: $border;
        text-style: bold;
        height: 1;
    }
    .form-section {
        border: round $border-form;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
        background: #050505;
        width: 1fr;
    }
    .section-label {
        color: $border;
        text-style: bold;
        margin-bottom: 1;
        height: 1;
    }
    .form-row {
        height: auto;
    }
    .form-col {
        width: 1fr;
        padding: 0 1 0 0;
        height: auto;
    }
    .form-col Label {
        color: $text-muted;
        height: 1;
        margin-top: 1;
    }
    .form-col Input {
        background: #0a0a0a;
        color: #EEEEEE;
        border: tall $border-blurred;
    }
    .form-col Input:focus {
        border: tall $border;
    }
    .form-section RadioSet {
        margin: 0 0 1 0;
        height: auto;
        background: #050505;
    }
    .form-section RadioButton {
        background: #050505;
        color: #999999;
    }
    #form-buttons {
        margin-top: 2;
        height: 5;
        align-horizontal: center;
    }
    #form-buttons Button {
        margin: 0 2;
    }
    #btn-launch {
        background: $border;
        color: #000000;
        text-style: bold;
    }
    #btn-launch:hover {
        background: $scrollbar-hover;
    }
    #btn-cancel {
        background: #1a1a1a;
        color: #999999;
        border: tall #333333;
    }

    /* ── Log Viewer ── */
    #log-header {
        dock: top;
        height: auto;
        background: #000000;
    }
    #log-controls {
        height: auto;
        padding: 1 1 0 1;
        layout: horizontal;
        background: #000000;
    }
    #log-autoscroll-row {
        height: 3;
        padding: 0 1;
        layout: horizontal;
        background: #000000;
    }
    #log-controls Select {
        width: 25;
        margin-right: 1;
        background: #0a0a0a;
    }
    #log-controls Input {
        width: 25;
        margin-right: 1;
        background: #0a0a0a;
        border: tall $border-blurred;
    }
    #log-controls Input:focus {
        border: tall $border;
    }
    #log-autoscroll-row Label {
        margin: 0 1 0 0;
        height: 3;
        content-align: center middle;
        color: $border;
    }
    #log-display {
        height: 1fr;
        border: round $border-card;
        margin: 0 1;
        background: #050505;
    }

    /* ── ASCII Lab ── */
    #ascii-lab-body {
        height: 1fr;
        align: center middle;
        background: #000000;
    }
    #lab-title {
        text-align: center;
        color: $border;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }
    #ascii-frame {
        width: auto;
        height: auto;
        content-align: center middle;
        text-align: center;
        min-height: 12;
        padding: 2 4;
        border: round $border-card;
        background: #050505;
    }
    #lab-status {
        text-align: center;
        height: 1;
        margin-top: 1;
        width: 100%;
    }
    """)

    TITLE = "ARTIC"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("1", "goto_dashboard", "Dashboard", priority=True),
        Binding("2", "goto_create", "Create", priority=True),
        Binding("3", "goto_logs", "Logs", priority=True),
        Binding("4", "goto_ascii_lab", "ASCII Lab", priority=True),
        Binding("5", "goto_leaderboard", "Leaderboard", priority=True),
    ]

    current_page: reactive[str] = reactive("Dashboard")
    total_pnl: reactive[float] = reactive(0.0)

    def __init__(self):
        super().__init__()
        import os
        hub_url = os.getenv("ARTIC_HUB_URL", "http://localhost:8000")
        self.manager = HubAdapter(hub_url=hub_url)
        self.register_theme(_build_bela_theme())
        self.theme = "bela"

    def on_mount(self) -> None:
        self.install_screen(LoginScreen(), name="login")
        self.install_screen(DashboardScreen(), name="dashboard")
        self.install_screen(CreateAgentScreen(), name="create")
        self.install_screen(LogViewerScreen(), name="logs")
        self.install_screen(AsciiLabScreen(), name="ascii_lab")
        self.push_screen("login")

    def action_goto_dashboard(self):
        self.switch_screen("dashboard")

    def action_goto_create(self):
        self.switch_screen("create")

    def action_goto_logs(self):
        self.switch_screen("logs")

    def action_goto_ascii_lab(self):
        self.switch_screen("ascii_lab")

    def action_goto_leaderboard(self):
        self.push_screen(LeaderboardScreen())


if __name__ == "__main__":
    BelaTUI().run()
