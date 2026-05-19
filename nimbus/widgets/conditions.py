"""
Conditions Widget for Nimbus

Displays current weather conditions and forecast in the left panel.
"""

from textual.reactive import reactive
from textual.widget import Widget
from rich.console import Group
from rich.text import Text


class Conditions(Widget):
    """Widget displaying weather conditions and forecast."""

    conditions = reactive(None)
    forecast = reactive([])
    morg_commentary: str = reactive("Morg is watching.")

    # Weather glyph mappings
    GLYPH_MAP: dict[str, str] = {
        "sunny": "☀",
        "clear": "☀",
        "cloud": "☁",
        "storm": "⛈",
        "thunder": "⛈",
        "rain": "🌧",
        "showers": "🌧",
        "snow": "❄",
        "fog": "░",
        "mist": "░",
    }

    def render(self) -> Group:
        """Render the conditions widget."""
        if not self.conditions:
            return Text(" ⚡ Loading conditions...", style="#d4a853")

        c = self.conditions

        # Header
        header = Text(" ⚡ conditions ", style="bold #d4a853")

        # Current conditions grid
        current_grid = Group(
            Text("CURRENT CONDITIONS", style="#9b97aa"),
            Text("──────────────────", style="#9b97aa"),
            Text(f"  🌡  {int(c.temp_f)}°F  ", style="bold #e8e4f0") + 
                Text(f"feels like {int(c.feels_like_f)}°F", style="#9b97aa"),
            Text(
                f"  💧  Humidity {int(c.humidity)}%  •  Dewpoint {int(c.dewpoint_f)}°F",
                style="#e8e4f0"
            ),
            Text(f"  💨  {int(c.wind_speed_mph)} mph {c.wind_dir}", style="#e8e4f0"),
            Text(
                f"  📊  Pressure {int(c.pressure_hpa)} hPa  {c.pressure_trend}",
                style="#e8e4f0"
            ),
            Text(f"  👁  Visibility {c.visibility_km:.1f} km", style="#e8e4f0"),
        )

        # Forecast lines
        forecast_lines = [
            Text("HOURLY FORECAST", style="#9b97aa"),
            Text("───────────────", style="#9b97aa")
        ]
        
        for p in self.forecast[:8]:
            time_str = p.start_time.strftime("%H:%M")
            glyph = self._get_weather_glyph(p.short_forecast)

            # Truncate description at word boundaries, max 16 chars
            desc = p.short_forecast
            if len(desc) > 16:
                desc = desc[:16].rsplit(' ', 1)[0]

            line = Text(
                f"  {time_str}  {int(p.temperature)}°  {glyph} {desc}",
                style="#e8e4f0"
            )
            forecast_lines.append(line)

        # Morg footer
        morg_footer = Group(
            Text("─────────────────", style="#9b97aa"),
            Text(self.morg_commentary, style="italic #d4a853")
        )

        return Group(
            header,
            current_grid,
            Text("\n"),
            Group(*forecast_lines),
            morg_footer
        )

    def _get_weather_glyph(self, desc: str) -> str:
        """Get the weather glyph for a description."""
        desc_lower = desc.lower()
        for key, glyph in self.GLYPH_MAP.items():
            if key in desc_lower:
                return glyph
        return "•"
