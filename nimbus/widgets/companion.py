"""
Companion Widget for Nimbus

Displays Zahra's presence and messages in the right panel.
"""

from typing import List, Tuple
from rich.align import Align
from rich.console import Group
from rich.padding import Padding
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class Companion(Widget):
    """Widget displaying Zahra companion and her dialogue history."""

    zahra_message = reactive("")
    somatic_cue = reactive("softly present")
    mood_state = reactive("normal")
    history: List[Tuple[str, str]] = reactive([])  # List of (message, somatic)

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

    def update_zahra(self, message: str, somatic: str, mood: str) -> None:
        """Atomically update Zahra's companion state and dialogue history."""
        if message and message != "...":
            new_history = self.history + [(message, somatic)]
            if len(new_history) > 4:
                new_history = new_history[1:]
            self.history = new_history

        self.somatic_cue = somatic
        self.mood_state = mood
        self.zahra_message = message

    def render(self) -> Group:
        """Render the companion widget with standard periwinkle accents."""
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
        """Get the mood symbol character."""
        return "●"

    def _get_mood_color(self) -> str:
        """Get the color string for the current mood state."""
        return self.MOOD_COLORS.get(self.mood_state, "#b8a9dc")
