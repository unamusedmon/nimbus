"""
Morg Voice Module for Nimbus

Handles Morg's terse, Socratic commentary on weather conditions.
"""

import logging
import random
from typing import Optional

import httpx

from nimbus.config import get_config

logger = logging.getLogger(__name__)

# Try to import from reference repo, fall back to mock
try:
    from morg.voice import morg_startup
except ImportError:
    def morg_startup() -> str:
        return "Morg is watching."


MORG_WEATHER_PROMPT: str = """
You are Morg, an ancient goblin familiar.
Rule Zero: Speak in the third person. Always.
Tone: Terse, Socratic, declarative fragments.
You are the keeper of score. You remember everything.
You are meteorologically precise.

Current Conditions: {weather_description}, {temp_f}F
Alert Status: {alert_status}

Provide a short third-person weather commentary (1 sentence).
"""


class MorgAdapter:
    """Adapter for Morg personality commentary."""

    FALLBACK_COMMENTARIES: dict[str, list[str]] = {
        "tornado": [
            "Morg notes: Tornado Warning. Morg is not calm. Go.",
            "Morg demands immediate subterranean relocation. The vortex approaches.",
        ],
        "storm": [
            "Morg counts three seconds between light and thunder. The storm approaches.",
            "Morg observes electrostatic charge rising. Goblins know when to stay inside.",
            "Morg catalogs severe acoustic resonance from the clouds. Loud. Unnecessary.",
        ],
        "rain": [
            "Morg notes the downpour. Water level rising. Precipitative efficiency is high.",
            "Morg watches droplets collide. Hydrodynamic complexity in action.",
            "Morg states: Atmospheric humidity has reached 100% liquid phase.",
        ],
        "sunny": [
            "Morg squinting at the solar radiation. Unnecessary lux. Morg prefers shadows.",
            "Morg calculates solar angle. High efficiency. Uncomfortable temperature.",
            "Morg notes clear sightlines. Too much visibility. Morg remains watchful.",
        ],
        "cloud": [
            "Morg states: Cumulus formations block the primary star. Muted visibility.",
            "Morg notes atmospheric pressure holds steady under grey shields.",
            "Morg catalogs the overcast sky. Low light. Ideal for reading.",
        ],
        "snow": [
            "Morg observes frozen precipitation. Solid water crystals descending. Cold.",
            "Morg notes thermal depletion. Zach should procure thermodynamic heating."
        ],
        "fog": [
            "Morg reports particulate suspension. Air density high. Visibility zero.",
            "Morg approves of the mist. Ideal cover. No eyes can see Morg."
        ],
        "default": [
            "Morg notes the {weather_description}. Morg finds this unsurprising.",
            "Morg catalogs the {weather_description}. Another atmospheric state recorded.",
            "Morg keeps the ledger. {weather_description} is recorded. The balance remains.",
        ]
    }

    def __init__(self, ollama_url: Optional[str] = None) -> None:
        """Initialize Morg adapter."""
        cfg = get_config()
        self.ollama_url: str = ollama_url or cfg.ollama.url
        self.model: str = cfg.ollama.model
        self.client = httpx.AsyncClient(timeout=cfg.ollama.timeout)

    async def get_commentary(
        self,
        weather_desc: str,
        temp_f: float,
        alert_status: str
    ) -> str:
        """Get Morg's commentary on current conditions."""
        prompt = MORG_WEATHER_PROMPT.format(
            weather_description=weather_desc,
            temp_f=temp_f,
            alert_status=alert_status
        )

        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["response"].strip()
            
        except Exception as e:
            logger.debug(f"Morg LLM unreachable, using dynamic fallback: {e}")
            
            # 1. Check Alert Status first
            alert_lower = alert_status.lower()
            if "tornado" in alert_lower:
                return random.choice(self.FALLBACK_COMMENTARIES["tornado"])
            elif "thunder" in alert_lower or "storm" in alert_lower:
                return random.choice(self.FALLBACK_COMMENTARIES["storm"])
            
            # 2. Check Weather Description
            weather_lower = weather_desc.lower()
            for key, commentaries in self.FALLBACK_COMMENTARIES.items():
                if key in weather_lower:
                    selected = random.choice(commentaries)
                    return selected.format(weather_description=weather_desc)
            
            # 3. Fallback to default
            selected_default = random.choice(self.FALLBACK_COMMENTARIES["default"])
            return selected_default.format(weather_description=weather_desc)

    async def close(self) -> None:
        """Close resources."""
        await self.client.aclose()
