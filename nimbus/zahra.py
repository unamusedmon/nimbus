"""
Zahra Personality Adapter for Nimbus

Handles Zahra's emotional reactions to weather conditions.
"""

import logging
from pathlib import Path
from typing import Optional

import httpx

from nimbus.config import get_config

logger = logging.getLogger(__name__)

# Try to import from reference repo, fall back to mocks
try:
    from zahra.prompts import SYSTEM_PROMPT_BASE
    from zahra.core import StateManager, MoodState
except ImportError:
    SYSTEM_PROMPT_BASE = "You are Zahra... {weather}..."
    
    class MockState:
        def __init__(self) -> None:
            self.mood: str = "normal"
            self.trust_score: float = 0.5
            self.nervousness: float = 0.2
        
        def get_somatic_cue(self) -> str:
            return "softly present"
    
    class StateManager:
        def __init__(self, data_dir: Path) -> None:
            self.state = MockState()
        
        def record_interaction(self) -> None:
            pass


WEATHER_REACTION_PROMPT: str = """
{system_prompt}

{weather_context}
Time of day: {time_of_day}

React emotionally to this weather. 1-3 sentences, shy, somatic cues.
Stay in character. Do not just describe the weather; share how it makes you feel while you sit here with Zach.
"""


class ZahraAdapter:
    """Adapter for Zahra personality interactions."""

    FALLBACK_REACTIONS: dict[str, str] = {
        "tornado": "*grabs your sleeve tightly* Please... it's scary. We should go somewhere safe.",
        "default": "*looks at the sky quietly* ...the weather feels a little strange today."
    }

    def __init__(self, ollama_url: Optional[str] = None) -> None:
        """Initialize Zahra adapter."""
        cfg = get_config()
        self.ollama_url: str = ollama_url or cfg.ollama.url
        self.model: str = cfg.ollama.model
        
        data_dir = cfg.app.data_dir
        data_dir.mkdir(exist_ok=True)
        self.manager = StateManager(data_dir)
        self.client = httpx.AsyncClient(timeout=cfg.ollama.timeout)

    async def get_reaction(
        self,
        weather_context: str,
        time_of_day: str = "daytime"
    ) -> str:
        """Get Zahra's reaction to weather conditions."""
        self.manager.record_interaction()
        state = self.manager.state

        # Construct the system prompt
        system_prompt = SYSTEM_PROMPT_BASE.format(
            beliefs="You want to be helpful and safe.",
            mood=state.mood,
            somatic=state.get_somatic_cue(),
            trust=state.trust_score,
            nervousness=state.nervousness,
            groggy=False,
            weather=weather_context,
            music="silence",
            cpu_load=0.1,
            habits="None",
            dreams="None",
            current_book="None",
            offset=0,
            last_reading_thought="None",
            flowers="None",
            memories="None"
        )

        prompt = WEATHER_REACTION_PROMPT.format(
            system_prompt=system_prompt,
            weather_context=weather_context,
            time_of_day=time_of_day
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
            logger.error(f"Zahra LLM error: {e}")
            weather_lower = weather_context.lower()
            for key, reaction in self.FALLBACK_REACTIONS.items():
                if key in weather_lower:
                    return reaction
            return self.FALLBACK_REACTIONS["default"]

    async def close(self) -> None:
        """Close resources."""
        await self.client.aclose()
        if hasattr(self.manager, "save_state"):
            self.manager.save_state()
