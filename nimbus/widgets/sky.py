"""
Sky Widget for Nimbus (Soulful)
"""

from datetime import datetime
from textual.widget import Widget
from textual.reactive import reactive
from rich.console import Group
from rich.text import Text
from rich.align import Align

class Sky(Widget):
    temp_f = reactive(0.0)
    description = reactive("Unknown")
    is_day = reactive(True)
    
    def render(self) -> Align:
        art = self._get_art()
        time_now = datetime.now().strftime("%H:%M:%S")
        
        header = Text(" ☁ nimbus ", style="#7ec8e3 bold", justify="center")
        location = Text("West Des Moines, IA", style="#9b97aa", justify="center")
        
        if self.description == "Unknown":
            content = Group(
                header,
                location,
                Text("\n" * 4),
                Text("Loading sky conditions...", style="italic #9b97aa", justify="center"),
                Text("\n" * 4),
                Text(time_now, style="#9b97aa", justify="center")
            )
            return Align.center(content, vertical="middle")

        big_temp = Text(f"{int(self.temp_f)}°", style="bold #e8e4f0", justify="center")
        desc = Text(self.description, style="italic #9b97aa", justify="center")
        
        live_time = Text(time_now, style="#9b97aa", justify="center")

        content = Group(
            header,
            location,
            Text("\n"),
            Align.center(Text(art, style=self._get_sky_color(), justify="center")),
            Text("\n"),
            big_temp,
            desc,
            Text("\n" * 3),
            live_time
        )
        return Align.center(content, vertical="middle")

    def _get_sky_color(self) -> str:
        desc = self.description.lower()
        if "storm" in desc or "thunder" in desc: return "#6b7fa3"
        if "cloud" in desc: return "#8b9bb4"
        if not self.is_day: return "#4a5568"
        return "#7ec8e3"

    def _get_art(self):
        desc = self.description.lower()
        if "sunny" in desc or "clear" in desc:
            if self.is_day:
                return r"""
      \   /
       .-.
    - (   ) -
       `-´
      /   \
                """
            else:
                return r"""
       ✦  ✧  ☽
      ✧  ✦  ✧
     ✦  ✧  ✦
                """
        elif "fog" in desc or "mist" in desc:
            return r"""
    ░░░░░░░░░░░
    ░░░░░░░░░░░
    ░░░░░░░░░░░
            """
        elif "snow" in desc:
            return r"""
         .--.
      .-(    ).
     (___.__)__)
      *  ❄  *
     ❄  *  ❄
            """
        elif "storm" in desc or "thunder" in desc:
            return r"""
         .--.
      .-(    ).
     (___.__)__)
        /_
         /
            """
        elif "rain" in desc or "showers" in desc:
            return r"""
         .--.
      .-(    ).
     (___.__)__)
      ' ' ' '
     ' ' ' '
            """
        elif "cloud" in desc:
            return r"""
         .--.
      .-(    ).
     (___.__)__)
            """
        return "☁"
