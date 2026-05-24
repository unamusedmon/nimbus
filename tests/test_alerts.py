"""
Unit tests for Nimbus Alert monitor
"""

import pytest
from unittest.mock import MagicMock

from nimbus.alerts import AlertMonitor, Alert


def test_alert_highest_severity_tornado() -> None:
    """Test that AlertMonitor correctly ranks active alerts with Tornado warnings being highest."""
    monitor = AlertMonitor()

    # Empty alerts
    assert monitor.get_highest_severity() is None

    # Normal alert
    alert_other = Alert(
        id="nws-alert-1",
        event="Flood Advisory",
        severity="Minor",
        certainty="Observed",
        urgency="Expected",
        headline="Flood Advisory active",
        description="A minor flood advisory exists"
    )
    monitor.active_alerts = [alert_other]
    assert monitor.get_highest_severity() is None  # Ranks as other / low priority

    # Severe Thunderstorm warning
    alert_severe = Alert(
        id="nws-alert-2",
        event="Severe Thunderstorm Warning",
        severity="Severe",
        certainty="Likely",
        urgency="Immediate",
        headline="Severe Thunderstorm Warning active",
        description="A severe thunderstorm warning exists"
    )
    monitor.active_alerts = [alert_other, alert_severe]
    assert monitor.get_highest_severity() == "Severe Thunderstorm"

    # Tornado Warning
    alert_tornado = Alert(
        id="nws-alert-3",
        event="Tornado Warning",
        severity="Extreme",
        certainty="Observed",
        urgency="Immediate",
        headline="TORNADO WARNING ACTIVE",
        description="Take cover immediately!"
    )
    monitor.active_alerts = [alert_other, alert_severe, alert_tornado]
    assert monitor.get_highest_severity() == "Tornado"


def test_desktop_notification_graceful_missing_binary() -> None:
    """Test that desktop notification gracefully handles subprocess missing notify-send without raising."""
    monitor = AlertMonitor()
    alert = Alert(
        id="nws-alert-test",
        event="Severe Weather Warning",
        severity="Severe",
        certainty="Likely",
        urgency="Immediate",
        headline="Severe warning headline",
        description="Severe warning description"
    )
    
    # Executing send_desktop_notification should complete without raising any exception,
    # even on machines without notify-send (it catches FileNotFoundError)
    try:
        monitor.send_desktop_notification(alert)
    except Exception as e:
        pytest.fail(f"send_desktop_notification raised exception: {e}")
