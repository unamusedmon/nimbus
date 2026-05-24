"""
Nimbus Main Entry Point

A beautiful Textual TUI weather app with Zahra and Morg.
"""

import asyncio
from datetime import datetime
from enum import Enum
import logging

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Static

from nimbus.config import get_config
from nimbus.weather import WeatherClient
from nimbus.alerts import AlertMonitor
from nimbus.zahra import ZahraAdapter
from nimbus.morg import MorgAdapter
from nimbus.theme import TCSS
from nimbus.widgets.sky import Sky
from nimbus.widgets.conditions import Conditions
from nimbus.widgets.companion import Companion

logger = logging.getLogger(__name__)


class ViewMode(str, Enum):
    """Available application layout views."""
    CURRENT = "CURRENT"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    DETAILS = "DETAILS"
    COMPANION = "COMPANION"


class Nimbus(App):
    """Nimbus Textual application with a multi-view navigation layer."""

    CSS = TCSS
    BINDINGS = [
        Binding("ctrl+t", "simulate_tornado", "Simulate Tornado"),
        Binding("ctrl+r", "refresh_data", "Refresh Data"),
        Binding("q", "safe_quit", "Quit"),
        Binding("1", "switch_view('CURRENT')", "Current View"),
        Binding("2", "switch_view('HOURLY')", "Hourly View"),
        Binding("3", "switch_view('DAILY')", "Daily View"),
        Binding("4", "switch_view('DETAILS')", "Details View"),
        Binding("5", "switch_view('COMPANION')", "Companion View"),
    ]

    # Reactive view state
    current_view = reactive(ViewMode.CURRENT)

    def __init__(self) -> None:
        """Initialize the Nimbus application."""
        super().__init__()
        
        self.weather_client = WeatherClient()
        self.alert_monitor = AlertMonitor()
        self.zahra = ZahraAdapter()
        self.morg = MorgAdapter()
        
        # State
        self.current_temp: float | None = None
        self.current_desc: str | None = None
        self.last_update_str: str = "Never"
        self.simulated_alert: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the application UI panels with native Header, Footer, and View Indicator."""
        yield Header(show_clock=True)
        yield Container(
            Vertical(Conditions(id="conditions"), id="left-panel"),
            Vertical(
                Sky(id="sky"),
                Static("[ current ]", id="view-indicator"),
                id="center-panel"
            ),
            Vertical(Companion(id="companion"), id="right-panel"),
            id="main-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the application timers and trigger background load."""
        cfg = get_config()
        self.title = cfg.app.name
        self.sub_title = cfg.location.city

        # Initial load in background task
        asyncio.create_task(self._initial_load())

        # Set up periodic updates
        self.set_interval(cfg.app.time_update_interval, self.update_time)
        self.set_interval(cfg.app.alert_poll_interval, self.update_alerts)
        self.set_interval(cfg.app.weather_poll_interval, self.update_weather)
        self.set_interval(
            cfg.app.ambient_poll_interval,
            self.ambient_personality_update
        )

    async def _initial_load(self) -> None:
        """Background task for loading weather and alert data sequentially before greeting."""
        # 1. Load atmospheric and alert data in parallel first
        await asyncio.gather(
            self.update_weather(),
            self.update_alerts()
        )
        # 2. Trigger the first personality update after data is loaded
        await self.personality_update("greeting")

    def update_time(self) -> None:
        """Update the ticking clock display and trigger clean sky re-rendering."""
        self.query_one("#sky").refresh()

    def action_switch_view(self, view: str) -> None:
        """Switch the current view mode."""
        try:
            self.current_view = ViewMode(view)
        except ValueError:
            logger.error(f"Invalid view mode requested: {view}")

    def watch_current_view(self, new_view: ViewMode) -> None:
        """Trigger updates and adjust panel layouts when the view mode shifts."""
        try:
            left = self.query_one("#left-panel")
            center = self.query_one("#center-panel")
            right = self.query_one("#right-panel")
        except Exception:
            # Catch initialization queries before widgets are mounted/yielded
            return

        # 1. Reset all layout classes
        for panel in (left, center, right):
            panel.remove_class("panel-hidden")
            panel.remove_class("panel-wide")
            panel.remove_class("panel-full")
            panel.remove_class("panel-details-left")
            panel.remove_class("panel-details-center")

        # 2. Add classes based on new_view
        if new_view == ViewMode.CURRENT:
            pass  # Standard width limits apply from CSS defaults
        elif new_view == ViewMode.HOURLY or new_view == ViewMode.DAILY:
            left.add_class("panel-hidden")
            center.add_class("panel-wide")
        elif new_view == ViewMode.DETAILS:
            left.add_class("panel-details-left")
            center.add_class("panel-details-center")
            right.add_class("panel-hidden")
        elif new_view == ViewMode.COMPANION:
            left.add_class("panel-hidden")
            center.add_class("panel-hidden")
            right.add_class("panel-full")

        # 3. Update the view indicator
        try:
            indicator = self.query_one("#view-indicator", Static)
            indicator.update(f"[ {new_view.name.lower()} ]")
        except Exception:
            pass

        # 4. Trigger personality update hook in parallel
        asyncio.create_task(self.personality_update(f"view:{new_view.name.lower()}"))

    async def action_refresh_data(self) -> None:
        """Force refresh all real-time data."""
        await asyncio.gather(
            self.update_weather(),
            self.update_alerts()
        )
        await self.personality_update("refresh")

    async def action_simulate_tornado(self) -> None:
        """Simulate a tornado warning for warning UI verification."""
        self.simulated_alert = "Tornado"
        await self.update_alerts()

        # Send desktop notification
        try:
            import subprocess
            subprocess.run(
                [
                    "notify-send",
                    "-u", "critical",
                    "NIMBUS ALERT",
                    "Simulated Tornado Warning! Go to basement!"
                ],
                check=False
            )
        except Exception:
            pass

    async def action_safe_quit(self) -> None:
        """Quit the application with a graceful goodbye from Zahra."""
        comp = self.query_one("#companion")
        comp.update_zahra(
            message="...stay safe out there.",
            somatic="looks up quietly",
            mood="normal"
        )
        await asyncio.sleep(1.5)
        self.exit()

    async def on_unmount(self) -> None:
        """Native lifecycle cleanup method to prevent resource leaks."""
        await asyncio.gather(
            self.weather_client.close(),
            self.alert_monitor.close(),
            self.zahra.close(),
            self.morg.close()
        )

    async def update_weather(self) -> None:
        """Update weather data from NWS."""
        try:
            conditions = await self.weather_client.get_current_conditions()
            forecast = await self.weather_client.get_hourly_forecast()

            cond_widget = self.query_one("#conditions", Conditions)
            sky_widget = self.query_one("#sky", Sky)

            cond_widget.conditions = conditions
            cond_widget.forecast = forecast

            sky_widget.temp_f = conditions.temp_f
            sky_widget.description = conditions.description
            sky_widget.is_day = 6 <= datetime.now().hour < 20

            self.last_update_str = datetime.now().strftime("%H:%M")

            # Check for significant weather changes (3°F delta or desc change)
            if (
                self.current_temp is None
                or abs(self.current_temp - conditions.temp_f) > 3.0
                or self.current_desc != conditions.description
            ):
                self.current_temp = conditions.temp_f
                self.current_desc = conditions.description
                await self.personality_update("weather_change")

        except Exception as e:
            self.notify(f"Weather update error: {e}", severity="error")

    async def update_alerts(self) -> None:
        """Update alert status from NWS."""
        await self.alert_monitor.check_alerts()
        severity = self.simulated_alert or self.alert_monitor.get_highest_severity()

        self.screen.remove_class("alert-active")
        self.screen.remove_class("tornado-active")

        if severity == "Tornado":
            self.screen.add_class("tornado-active")
            await self.personality_update("TORNADO WARNING")
        elif severity == "Severe Thunderstorm":
            self.screen.add_class("alert-active")
            await self.personality_update("SEVERE THUNDERSTORM WARNING")

    async def personality_update(self, reason: str) -> None:
        """Update personality responses based on current conditions."""
        if self.current_desc is None:
            weather_desc = "unknown"
        else:
            weather_desc = self.current_desc

        temp_f = self.current_temp or 0.0

        # Determine time of day
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        # Construct weather context for companions
        alert_severity = self.simulated_alert or self.alert_monitor.get_highest_severity()
        alert_status = (
            f"Alert status: {alert_severity}." if alert_severity else "No active alerts."
        )
        weather_context = (
            f"It's {int(temp_f)}°F outside. {weather_desc}. {alert_status}"
        )

        # Get Morg's commentary
        morg_text = await self.morg.get_commentary(
            weather_desc, temp_f, alert_severity or "None"
        )
        self.query_one("#conditions").morg_commentary = morg_text

        # Get Zahra's reaction
        zahra_text = await self.zahra.get_reaction(weather_context, time_of_day=time_of_day)
        comp = self.query_one("#companion")
        
        # Read the real StateManager variables safely if they exist
        somatic = "softly present"
        mood = "normal"
        if hasattr(self.zahra, "manager") and hasattr(self.zahra.manager, "state"):
            state = self.zahra.manager.state
            if hasattr(state, "get_somatic_cue"):
                somatic = state.get_somatic_cue()
            if hasattr(state, "mood"):
                mood = str(state.mood)

        comp.update_zahra(
            message=zahra_text,
            somatic=somatic,
            mood=mood
        )

    async def ambient_personality_update(self) -> None:
        """Periodic ambient companion dialogue update."""
        await self.personality_update("ambient")


def run() -> None:
    """Run the Nimbus application."""
    app = Nimbus()
    app.run()


if __name__ == "__main__":
    run()
