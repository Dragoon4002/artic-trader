"""Login/Register screen for Artic TUI."""
from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, Label
from textual import work


class LoginScreen(Screen):
    """Login or register screen shown on startup."""

    def compose(self) -> ComposeResult:
        # Import COLORS and ARTIC_ASCII from tui.py after we update it
        # For now use placeholder
        from .tui import COLORS, ARTIC_ASCII

        ac = COLORS["accent_1"]
        yield Static(ARTIC_ASCII, id="login-banner")
        with Vertical(id="login-container"):
            yield Label("Welcome to Artic", id="login-title")
            with Vertical(id="login-form"):
                yield Label("Email", classes="login-label")
                yield Input(placeholder="user@example.com", id="login-email")
                yield Label("Password", classes="login-label")
                yield Input(placeholder="password", password=True, id="login-password")
                with Horizontal(id="login-buttons"):
                    yield Button("Login", variant="primary", id="btn-login")
                    yield Button("Register", variant="default", id="btn-register")

    def on_mount(self) -> None:
        self.app.current_page = "Login"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-login":
            self._do_login()
        elif event.button.id == "btn-register":
            self._do_register()

    @work(exclusive=False)
    async def _do_login(self) -> None:
        email = self.query_one("#login-email", Input).value.strip()
        password = self.query_one("#login-password", Input).value
        if not email or not password:
            self.notify("Email and password required", severity="error")
            return
        try:
            await self.app.manager.login(email, password)
            self.notify(f"Logged in as {email}")
            await self.app.manager.refresh_agents()
            self.app.switch_screen("dashboard")
        except Exception as e:
            self.notify(f"Login failed: {e}", severity="error")

    @work(exclusive=False)
    async def _do_register(self) -> None:
        email = self.query_one("#login-email", Input).value.strip()
        password = self.query_one("#login-password", Input).value
        if not email or not password:
            self.notify("Email and password required", severity="error")
            return
        try:
            await self.app.manager.register(email, password)
            self.notify(f"Registered and logged in as {email}")
            await self.app.manager.refresh_agents()
            self.app.switch_screen("dashboard")
        except Exception as e:
            self.notify(f"Registration failed: {e}", severity="error")


# CSS to be merged into main tui.py CSS
LOGIN_CSS = """
    #login-banner {
        dock: top;
        height: 8;
        background: #000000;
        color: $border;
        padding: 1 2 0 2;
        text-align: center;
        border-bottom: solid $border-blurred;
    }
    #login-container {
        height: 1fr;
        align: center middle;
        background: #000000;
    }
    #login-title {
        text-align: center;
        color: $border;
        text-style: bold;
        height: 1;
        margin-bottom: 2;
    }
    #login-form {
        width: 50;
        border: round $border-card;
        padding: 2 3;
        background: #050505;
    }
    .login-label {
        color: $text-muted;
        height: 1;
        margin-top: 1;
    }
    #login-email, #login-password {
        background: #0a0a0a;
        color: #EEEEEE;
        border: tall $border-blurred;
        margin-bottom: 1;
    }
    #login-email:focus, #login-password:focus {
        border: tall $border;
    }
    #login-buttons {
        height: 5;
        margin-top: 2;
        align-horizontal: center;
    }
    #login-buttons Button {
        margin: 0 1;
    }
    #btn-login {
        background: $border;
        color: #000000;
        text-style: bold;
    }
    #btn-login:hover {
        background: $scrollbar-hover;
    }
    #btn-register {
        background: #1a1a1a;
        color: #999999;
        border: tall #333333;
    }
"""
