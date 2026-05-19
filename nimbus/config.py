"""
Nimbus Configuration Module

Centralized configuration for the Nimbus weather application.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class LocationConfig:
    """Geographic location configuration."""
    lat: float = 41.5401
    lon: float = -93.6271
    city: str = "West Des Moines, IA"
    grid_id: str = "DMX"
    grid_x: int = 73
    grid_y: int = 47


@dataclass(frozen=True)
class APIConfig:
    """API configuration for external services."""
    weather_base_url: str = "https://api.weather.gov"
    user_agent: str = "NimbusWeatherApp/0.1.0 (zach@example.com)"
    timeout: float = 10.0
    

@dataclass(frozen=True)
class OllamaConfig:
    """Ollama LLM configuration."""
    url: str = "http://localhost:11434"
    model: str = "gemma3:12b"
    timeout: float = 30.0


@dataclass(frozen=True)
class AppConfig:
    """Application configuration."""
    name: str = "Nimbus"
    version: str = "0.1.0"
    weather_poll_interval: int = 900  # seconds (15 minutes)
    alert_poll_interval: int = 120  # seconds (2 minutes)
    ambient_poll_interval: int = 1200  # seconds (20 minutes)
    time_update_interval: int = 1  # seconds
    data_dir: Path = Path("./zahra_data")


@dataclass(frozen=True)
class NimbusConfig:
    """Main configuration container."""
    location: LocationConfig = LocationConfig()
    api: APIConfig = APIConfig()
    ollama: OllamaConfig = OllamaConfig()
    app: AppConfig = AppConfig()


# Global configuration instance
config = NimbusConfig()


def get_config() -> NimbusConfig:
    """Get the global configuration instance."""
    return config
