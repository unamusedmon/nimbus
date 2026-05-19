"""
Morg Voice Module for Nimbus

Handles Morg's terse, Socratic commentary on weather conditions.
"""

import logging
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

    FALLBACK_COMMENTARIES: dict[str, str] = {
        "tornado": "Morg notes: Tornado Warning. Morg is not calm. Go.",
        "default": "Morg notes the {weather_description}. Morg finds this unsurprising."
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
            logger.error(f"Morg LLM error: {e}")
            alert_lower = alert_status.lower()
            for key, commentary in self.FALLBACK_COMMENTARIES.items():
                if key in alert_lower:
                    return commentary
            return self.FALLBACK_COMMENTARIES["default"].format(
                weather_description=weather_desc
            )

    async def close(self) -> None:
        """Close resources."""
        await self.client.aclose()
