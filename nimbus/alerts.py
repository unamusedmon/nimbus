"""
Alert Monitoring for Nimbus

Handles active weather alerts and desktop notifications.
"""

import logging
import subprocess
from datetime import datetime
from typing import List, Optional

import httpx
from pydantic import BaseModel

from nimbus.config import get_config

logger = logging.getLogger(__name__)


class Alert(BaseModel):
    """Represents a weather alert."""
    id: str
    event: str
    severity: str
    certainty: str
    urgency: str
    headline: str
    description: str
    instruction: Optional[str] = None
    ends: Optional[datetime] = None


class AlertMonitor:
    """Monitor for weather alerts from NWS API."""

    SEVERITY_PRIORITY: list[str] = ["Tornado", "Severe Thunderstorm", "Other"]
    HIGH_SEVERITY_LEVELS: set[str] = {"Severe", "Extreme"}

    def __init__(self) -> None:
        """Initialize the alert monitor."""
        cfg = get_config()
        self.client = httpx.AsyncClient(
            headers={"User-Agent": cfg.api.user_agent},
            timeout=cfg.api.timeout
        )
        self.active_alerts: List[Alert] = []

    async def check_alerts(self) -> List[Alert]:
        """Check for active weather alerts."""
        cfg = get_config()
        alerts_url = (
            f"{cfg.api.weather_base_url}/alerts/active?"
            f"point={cfg.location.lat},{cfg.location.lon}"
        )
        
        try:
            response = await self.client.get(alerts_url)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            
            new_alerts = []
            for feature in features:
                props = feature["properties"]
                alert = Alert(
                    id=props["id"],
                    event=props["event"],
                    severity=props["severity"],
                    certainty=props["certainty"],
                    urgency=props["urgency"],
                    headline=props["headline"],
                    description=props["description"],
                    instruction=props.get("instruction"),
                    ends=datetime.fromisoformat(props["ends"]) if props.get("ends") else None
                )
                new_alerts.append(alert)

            # Check for new high-severity alerts to notify
            existing_ids = {a.id for a in self.active_alerts}
            for alert in new_alerts:
                if alert.id not in existing_ids and alert.severity in self.HIGH_SEVERITY_LEVELS:
                    self.send_desktop_notification(alert)

            self.active_alerts = new_alerts
            return self.active_alerts
            
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
            return self.active_alerts

    def send_desktop_notification(self, alert: Alert) -> None:
        """Send desktop notification for a high-severity alert."""
        try:
            subprocess.run(
                ["notify-send", "-u", "critical", f"NIMBUS: {alert.event}", alert.headline],
                check=False
            )
        except FileNotFoundError:
            logger.warning("notify-send not found. Desktop notification skipped.")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    def get_highest_severity(self) -> Optional[str]:
        """Get the highest severity alert type."""
        if not self.active_alerts:
            return None
        
        events = [a.event.lower() for a in self.active_alerts]
        
        for severity_type in self.SEVERITY_PRIORITY:
            if any(severity_type.lower() in e for e in events):
                return severity_type
        
        return None
