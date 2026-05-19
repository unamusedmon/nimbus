"""
Companion Widget for Nimbus

Displays Zahra's presence and messages in the right panel.
"""

from textual.reactive import reactive
from textual.widget import Widget
from rich.align import Align
from rich.console import Group
from rich.text import Text
from rich.padding import Padding


class Companion(Widget):
    """Widget displaying Zahra companion."""

    zahra_message: str = reactive("")
    somatic_cue: str = reactive("softly present")
    mood_state: str = reactive("normal")
    history: list = reactive([])  # List of (message, somatic)

    ZAHRA_CHIBI: str = r"""
     (\_/__)
     (='.'=)
     (")_(")
    """

    # Mood color mappings
    MOOD_COLORS: dict[str, str] = {
        "curious": "#ffb7c5",
        "playful": "#ffb7c5",
        "withdrawn": "#9b97aa",
        "normal": "#b8a9dc",
    }

    def watch_zahra_message(self, new_msg: str) -> None:
        """Watch for zahra message changes and update history."""
        if new_msg and new_msg != "...":
            self.history = self.history + [(new_msg, self.somatic_cue)]
            if len(self.history) > 4:
                self.history = self.history[1:]

    def render(self) -> Group:
        """Render the companion widget."""
        header = Text(" ✦ zahra ", style="#b8a9dc bold")
        chibi = Text(self.ZAHRA_CHIBI, style="#c9bfe8")
        mood_dot = Text(self._get_mood_symbol(), style=self._get_mood_color())

        history_group = []
        for i, (msg, somatic) in enumerate(self.history):
            is_latest = (i == len(self.history) - 1)
            style = "#b8a9dc" if is_latest else "#9b97aa"

            parts = []
            if somatic:
                cue_style = "italic #c9bfe8" if is_latest else "italic #9b97aa"
                parts.append(Text(f"*{somatic}* ", style=cue_style))

            parts.append(Text(msg, style=style))
            history_group.append(Group(*parts))
            history_group.append(Text(""))

        return Group(
            Align.center(Group(
                Align.center(header),
                Align.center(chibi),
                Align.center(mood_dot)
            )),
            Text("\n"),
            Padding(Group(*history_group), (0, 2))
        )

    def _get_mood_symbol(self) -> str:
        """Get the mood symbol."""
        return "●"

    def _get_mood_color(self) -> str:
        """Get the color for the current mood."""
        return self.MOOD_COLORS.get(self.mood_state, "#b8a9dc")
