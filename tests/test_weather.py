"""
Unit tests for Nimbus Weather module
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from nimbus.weather import WeatherPeriod, WeatherClient


def test_weather_period_pydantic_parsing() -> None:
    """Test that WeatherPeriod correctly parses camelCase API inputs and maps them to snake_case."""
    raw_api_payload = {
        "number": 1,
        "name": "Tonight",
        "startTime": "2026-05-24T18:00:00-05:00",
        "endTime": "2026-05-24T19:00:00-05:00",
        "isDaytime": False,
        "temperature": 72.0,
        "temperatureUnit": "F",
        "windSpeed": "10 mph",
        "windDirection": "SSE",
        "icon": "https://api.weather.gov/icons/land/night/tsra",
        "shortForecast": "Showers And Thunderstorms Likely",
        "detailedForecast": "Showers and thunderstorms likely tonight. Cloudy with a low around 68."
    }

    # Deserialization using camelCase aliases
    period = WeatherPeriod(**raw_api_payload)

    assert period.number == 1
    assert period.name == "Tonight"
    assert period.start_time == datetime.fromisoformat("2026-05-24T18:00:00-05:00")
    assert period.end_time == datetime.fromisoformat("2026-05-24T19:00:00-05:00")
    assert period.is_daytime is False
    assert period.temperature == 72.0
    assert period.temperature_unit == "F"
    assert period.wind_speed == "10 mph"
    assert period.wind_direction == "SSE"
    assert period.icon == "https://api.weather.gov/icons/land/night/tsra"
    assert period.short_forecast == "Showers And Thunderstorms Likely"
    assert period.detailed_forecast == "Showers and thunderstorms likely tonight. Cloudy with a low around 68."


def test_weather_period_pydantic_parsing_snake_case() -> None:
    """Test that WeatherPeriod can also be instantiated directly with snake_case parameters."""
    period = WeatherPeriod(
        number=2,
        name="Tomorrow",
        start_time=datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 5, 25, 9, 0, tzinfo=timezone.utc),
        is_daytime=True,
        temperature=85.0,
        temperature_unit="F",
        wind_speed="12 mph",
        wind_direction="S",
        icon="https://api.weather.gov/icons/land/day/sunny",
        short_forecast="Sunny",
        detailed_forecast="Sunny and warm."
    )

    assert period.number == 2
    assert period.start_time.hour == 8
    assert period.is_daytime is True


def test_weather_client_normalization() -> None:
    """Test NWS weather condition string normalization to human-friendly phrases."""
    client = WeatherClient()
    
    assert client.normalize_condition("Mostly Cloudy") == "It is mostly cloudy"
    assert client.normalize_condition("clear") == "The skies are clear"
    assert client.normalize_condition("sunny") == "It is sunny outside"
    assert client.normalize_condition("random condition") == "The weather is random condition"


def test_weather_client_truncation() -> None:
    """Test smart text truncation at word boundaries for TUI layouts."""
    client = WeatherClient()

    # Exact fits
    assert client.truncate_smart("Sunny", 16) == "Sunny"

    # Truncate at word boundary within limit
    assert client.truncate_smart("Showers and Storms", 16) == "Showers and"

    # Edge cases
    assert client.truncate_smart("Storm", 3) == "Sto"
