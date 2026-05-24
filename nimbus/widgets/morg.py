"""
Morg Widget for Nimbus

Displays Morg's Socratic presence and commentaries in the center-right domain.
"""

from datetime import datetime
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class Morg(Widget):
    """Widget displaying Morg companion and Socratic commentaries."""

    morg_commentary = reactive("Morg is watching.")
    last_observed = reactive("")

    # Angular, geometric, watchful goblin ASCII art
    MORG_ASCII: str = r"""
     ▲___▲
    / • ▵ • \
   |  \___/  |
   \  / ▵ \  /
    ▼       ▼
    """

    def watch_morg_commentary(self, new_commentary: str) -> None:
        """Watch for commentary updates and update timestamp dynamically."""
        self.last_observed = datetime.now().strftime("%H:%M:%S")
        try:
            self.query_one("#morg-commentary-text", Static).update(new_commentary)
        except Exception:
            pass

    def watch_last_observed(self, new_time: str) -> None:
        """Watch for timestamp changes and update display."""
        try:
            self.query_one("#morg-obs-time", Static).update(f"last observed: {new_time}")
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Compose child components and assign target CSS classes."""
        yield Static(" ⚡ morg ", classes="morg-widget-header")
        yield Static(self.MORG_ASCII.strip("\n"), classes="morg-ascii")
        yield Static("●", classes="morg-mood-dot")
        yield Static(self.morg_commentary, id="morg-commentary-text", classes="morg-text")
        yield Static(
            f"last observed: {self.last_observed or 'Never'}",
            id="morg-obs-time",
            classes="morg-timestamp"
        )
