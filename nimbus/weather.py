"""
Weather Module for Nimbus

Handles fetching data from the National Weather Service API.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from pydantic import BaseModel, Field
from nimbus.config import get_config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.weather.gov"
USER_AGENT = "NimbusWeatherApp/0.1.0 (zach@example.com)"

class WeatherPeriod(BaseModel):
    number: int
    name: Optional[str] = None
    startTime: datetime
    endTime: datetime
    isDaytime: bool
    temperature: float
    temperatureUnit: str
    windSpeed: str
    windDirection: str
    icon: str
    shortForecast: str
    detailedForecast: str

class GridValue(BaseModel):
    validTime: str
    value: float

class GridParameter(BaseModel):
    uom: str
    values: List[GridValue]

class GridData(BaseModel):
    temperature: Optional[GridParameter] = None
    relativeHumidity: Optional[GridParameter] = None
    dewpoint: Optional[GridParameter] = None
    windSpeed: Optional[GridParameter] = None
    windDirection: Optional[GridParameter] = None
    barometricPressure: Optional[GridParameter] = None
    visibility: Optional[GridParameter] = None
    apparentTemperature: Optional[GridParameter] = None

class CurrentConditions(BaseModel):
    temp_f: float
    feels_like_f: float
    humidity: float
    dewpoint_f: float
    wind_speed_mph: float
    wind_dir: str
    pressure_hpa: float
    pressure_trend: str = "→" # ↑ ↓ →
    visibility_km: float
    description: str
    timestamp: datetime

class WeatherClient:
    def __init__(self):
        cfg = get_config()
        self.client = httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=15.0)
        self.grid_id: str = cfg.location.office
        self.grid_x: int = cfg.location.grid_x
        self.grid_y: int = cfg.location.grid_y
        self.last_pressure: Optional[float] = None

    async def get_hourly_forecast(self) -> List[WeatherPeriod]:
        url = f"{BASE_URL}/gridpoints/{self.grid_id}/{self.grid_x},{self.grid_y}/forecast/hourly"
        resp = await self.client.get(url)
        resp.raise_for_status()
        data = resp.json()
        periods = data["properties"]["periods"]
        for p in periods:
            p["shortForecast"] = self.normalize_condition(p["shortForecast"])
        return [WeatherPeriod(**p) for p in periods]

    def _find_current_grid_value(self, parameter: Optional[GridParameter]) -> Optional[float]:
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
        """Convert NWS condition strings to human-readable full sentences."""
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
        """Truncate at word boundaries, max max_chars."""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars].rsplit(' ', 1)[0]
        return truncated if len(truncated) > 0 else text[:max_chars]

    async def get_current_conditions(self, forecast: List[WeatherPeriod] = None) -> CurrentConditions:
        url = f"{BASE_URL}/gridpoints/{self.grid_id}/{self.grid_x},{self.grid_y}"
        resp = await self.client.get(url)
        resp.raise_for_status()
        raw_data = resp.json()["properties"]
        grid = GridData(**raw_data)

        if not forecast:
            forecast = await self.get_hourly_forecast()
        
        current_period = forecast[0]

        feels_like_c = self._find_current_grid_value(grid.apparentTemperature)
        dewpoint_c = self._find_current_grid_value(grid.dewpoint)
        pressure_pa = self._find_current_grid_value(grid.barometricPressure)
        visibility_m = self._find_current_grid_value(grid.visibility)
        
        def c_to_f(c): return (c * 9/5) + 32 if c is not None else current_period.temperature
        
        pressure_hpa = (pressure_pa / 100.0) if pressure_pa else 1013.25
        trend = "→"
        if self.last_pressure is not None:
            if pressure_hpa > self.last_pressure + 0.1: trend = "↑"
            elif pressure_hpa < self.last_pressure - 0.1: trend = "↓"
        self.last_pressure = pressure_hpa

        return CurrentConditions(
            temp_f=current_period.temperature,
            feels_like_f=c_to_f(feels_like_c),
            humidity=self._find_current_grid_value(grid.relativeHumidity) or 0,
            dewpoint_f=c_to_f(dewpoint_c),
            wind_speed_mph=float(current_period.windSpeed.split(" ")[0]),
            wind_dir=current_period.windDirection,
            pressure_hpa=pressure_hpa,
            pressure_trend=trend,
            visibility_km=(visibility_m / 1000.0) if visibility_m else 10.0,
            description=self.normalize_condition(current_period.shortForecast),
            timestamp=datetime.now()
        )

    async def close(self):
        await self.client.aclose()
