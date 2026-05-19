"""
Nimbus Main Entry Point

A beautiful Textual TUI weather app with Zahra and Morg.
"""

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from nimbus.config import get_config
from nimbus.weather import WeatherClient
from nimbus.alerts import AlertMonitor
from nimbus.zahra import ZahraAdapter
from nimbus.morg import MorgAdapter
from nimbus.theme import TCSS
from nimbus.widgets.sky import Sky
from nimbus.widgets.conditions import Conditions
from nimbus.widgets.companion import Companion


class Nimbus(App):
    """Nimbus Textual application."""

    CSS = TCSS
    BINDINGS = [
        Binding("ctrl+t", "simulate_tornado", "Simulate Tornado"),
        Binding("ctrl+r", "refresh_data", "Refresh Data"),
        Binding("q", "safe_quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize the Nimbus application."""
        super().__init__()
        cfg = get_config()
        
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
        """Compose the application UI."""
        yield Container(
            Vertical(Conditions(id="conditions"), id="left-panel"),
            Vertical(Sky(id="sky"), id="center-panel"),
            Vertical(Companion(id="companion"), id="right-panel"),
            id="main-container"
        )
        yield Static(id="app-footer")

    async def on_mount(self) -> None:
        """Initialize the application on mount."""
        cfg = get_config()
        self.title = cfg.app.name
        self.sub_title = cfg.location.city

        # Initial data fetch and personality updates in parallel
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
        """Background task for initial data load."""
        await asyncio.gather(
            self.update_weather(),
            self.update_alerts(),
            self.personality_update("greeting")
        )

    def update_time(self) -> None:
        """Update the time display and trigger sky re-render."""
        self.query_one("#sky").mutate_reactive(Sky.is_day)
        footer = self.query_one("#app-footer")
        footer.update(
            f"Last update: {self.last_update_str} | "
            f"Polling: Active | {get_config().app.name} v{get_config().app.version}"
        )

    async def action_refresh_data(self) -> None:
        """Force refresh all data."""
        await asyncio.gather(
            self.update_weather(),
            self.update_alerts(),
            self.personality_update("refresh")
        )

    async def action_simulate_tornado(self) -> None:
        """Simulate a tornado warning for testing."""
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
        """Quit the application with a goodbye from Zahra."""
        comp = self.query_one("#companion")
        comp.zahra_message = " *looks up quietly* ...stay safe out there."
        await asyncio.sleep(1.5)
        
        # Clean up resources
        await asyncio.gather(
            self.weather_client.close(),
            self.alert_monitor.close(),
            self.zahra.close(),
            self.morg.close()
        )
        self.exit()

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

            # Check for significant weather changes
            if (
                self.current_temp is None
                or abs(self.current_temp - conditions.temp_f) > 3
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

        # Construct weather context for Zahra
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
        comp.mood_state = str(self.zahra.manager.state.mood)
        comp.somatic_cue = self.zahra.manager.state.get_somatic_cue()
        comp.zahra_message = zahra_text

    async def ambient_personality_update(self) -> None:
        """Periodic ambient personality update."""
        await self.personality_update("ambient")


def run() -> None:
    """Run the Nimbus application."""
    app = Nimbus()
    app.run()


if __name__ == "__main__":
    run()
