"""
Weather Module for Nimbus

Handles fetching data from the National Weather Service API.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from pydantic import BaseModel, Field, ConfigDict
from nimbus.config import get_config

logger = logging.getLogger(__name__)


class WeatherPeriod(BaseModel):
    """Represents a forecast period from the NWS."""
    number: int
    name: Optional[str] = None
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    is_daytime: bool = Field(alias="isDaytime")
    temperature: float
    temperature_unit: str = Field(alias="temperatureUnit")
    wind_speed: str = Field(alias="windSpeed")
    wind_direction: str = Field(alias="windDirection")
    icon: str
    short_forecast: str = Field(alias="shortForecast")
    detailed_forecast: str = Field(alias="detailedForecast")

    model_config = ConfigDict(populate_by_name=True)


class GridValue(BaseModel):
    """Represents a value at a specific time in grid coordinates."""
    validTime: str
    value: float


class GridParameter(BaseModel):
    """Represents a list of values for a specific weather parameter."""
    uom: str
    values: List[GridValue]


class GridData(BaseModel):
    """Represents current raw grid data parsed from the NWS point API."""
    temperature: Optional[GridParameter] = None
    relative_humidity: Optional[GridParameter] = Field(None, alias="relativeHumidity")
    dewpoint: Optional[GridParameter] = None
    wind_speed: Optional[GridParameter] = Field(None, alias="windSpeed")
    wind_direction: Optional[GridParameter] = Field(None, alias="windDirection")
    barometric_pressure: Optional[GridParameter] = Field(None, alias="barometricPressure")
    visibility: Optional[GridParameter] = None
    apparent_temperature: Optional[GridParameter] = Field(None, alias="apparentTemperature")

    model_config = ConfigDict(populate_by_name=True)


class CurrentConditions(BaseModel):
    """Normalized real-time weather conditions."""
    temp_f: float
    feels_like_f: float
    humidity: float
    dewpoint_f: float
    wind_speed_mph: float
    wind_dir: str
    pressure_hpa: float
    pressure_trend: str = "→"  # ↑ ↓ →
    visibility_km: float
    description: str
    timestamp: datetime


class WeatherClient:
    """NWS API client that retrieves and processes meteorological data."""

    def __init__(self) -> None:
        """Initialize the weather client using shared configuration."""
        cfg = get_config()
        self.base_url: str = cfg.api.weather_base_url
        self.client = httpx.AsyncClient(
            headers={"User-Agent": cfg.api.user_agent},
            timeout=cfg.api.timeout
        )
        self.grid_id: str = cfg.location.grid_id
        self.grid_x: int = cfg.location.grid_x
        self.grid_y: int = cfg.location.grid_y
        self.last_pressure: Optional[float] = None

    async def get_hourly_forecast(self) -> List[WeatherPeriod]:
        """Retrieve the hourly weather forecast."""
        url = f"{self.base_url}/gridpoints/{self.grid_id}/{self.grid_x},{self.grid_y}/forecast/hourly"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            periods = data["properties"]["periods"]
            return [WeatherPeriod(**p) for p in periods]
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error(f"Failed to fetch hourly forecast from NWS: {e}")
            raise

    def _find_current_grid_value(self, parameter: Optional[GridParameter]) -> Optional[float]:
        """Find the grid value applicable to the current timestamp."""
        if not parameter or not parameter.values:
            return None
        now = datetime.now(timezone.utc)
        val = parameter.values[0].value
        for entry in parameter.values:
            start_str = entry.validTime.split("/")[0]
            start_time = datetime.fromisoformat(start_str)
            if start_time <= now:
                val = entry.value
            else:
                break
        return val

    def normalize_condition(self, raw: str) -> str:
        """Convert NWS condition strings to beautiful, human-readable full sentences."""
        raw = raw.lower().strip()
        replacements = {
            "showers and thunderstorms likely": "There are storms likely tonight",
            "showers and thunderstorms": "There are thunderstorms rolling through",
            "chance showers and thunderstorms": "There is a chance of storms",
            "chance rain showers": "There is light rain possible",
            "rain showers likely": "Rain is likely",
            "slight chance showers and thunderstorms": "There is a small chance of storms",
            "mostly cloudy": "It is mostly cloudy",
            "partly cloudy": "It is partly cloudy",
            "mostly clear": "It is mostly clear",
            "clear": "The skies are clear",
            "sunny": "It is sunny outside",
            "fog": "It is foggy out",
            "snow": "There is snow falling",
        }
        for nws_string, human_string in replacements.items():
            if nws_string in raw:
                return human_string
        return f"The weather is {raw}"

    def truncate_smart(self, text: str, max_chars: int = 16) -> str:
        """Truncate at word boundaries to preserve clean visual layouts, max max_chars."""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars].rsplit(' ', 1)[0]
        return truncated if len(truncated) > 0 else text[:max_chars]

    async def get_current_conditions(self, forecast: List[WeatherPeriod] = None) -> CurrentConditions:
        """Retrieve real-time atmospheric measurements from raw grid coordinates."""
        url = f"{self.base_url}/gridpoints/{self.grid_id}/{self.grid_x},{self.grid_y}"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            raw_data = resp.json()["properties"]
            grid = GridData(**raw_data)

            if not forecast:
                forecast = await self.get_hourly_forecast()
            
            current_period = forecast[0]

            feels_like_c = self._find_current_grid_value(grid.apparent_temperature)
            dewpoint_c = self._find_current_grid_value(grid.dewpoint)
            pressure_pa = self._find_current_grid_value(grid.barometric_pressure)
            visibility_m = self._find_current_grid_value(grid.visibility)
            
            def c_to_f(c):
                return (c * 9 / 5) + 32 if c is not None else current_period.temperature
            
            pressure_hpa = (pressure_pa / 100.0) if pressure_pa else 1013.25
            trend = "→"
            if self.last_pressure is not None:
                if pressure_hpa > self.last_pressure + 0.1:
                    trend = "↑"
                elif pressure_hpa < self.last_pressure - 0.1:
                    trend = "↓"
            self.last_pressure = pressure_hpa

            # Split wind speed text to float conversion
            try:
                wind_speed_val = float(current_period.wind_speed.split(" ")[0])
            except (ValueError, IndexError):
                wind_speed_val = 0.0

            return CurrentConditions(
                temp_f=current_period.temperature,
                feels_like_f=c_to_f(feels_like_c),
                humidity=self._find_current_grid_value(grid.relative_humidity) or 0.0,
                dewpoint_f=c_to_f(dewpoint_c),
                wind_speed_mph=wind_speed_val,
                wind_dir=current_period.wind_direction,
                pressure_hpa=pressure_hpa,
                pressure_trend=trend,
                visibility_km=(visibility_m / 1000.0) if visibility_m else 10.0,
                description=self.normalize_condition(current_period.short_forecast),
                timestamp=datetime.now()
            )
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error(f"Failed to fetch current grid conditions from NWS: {e}")
            raise

    async def close(self) -> None:
        """Asynchronously close the client's connection pool."""
        await self.client.aclose()
