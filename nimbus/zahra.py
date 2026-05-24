"""
Zahra Personality Adapter for Nimbus

Handles Zahra's emotional reactions to weather conditions.
"""

import logging
import random
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
            self.cues: list[str] = [
                "softly present",
                "fidgeting with her sleeve",
                "looking down shyly",
                "tentatively hopeful",
                "peeking up through her lashes",
                "adjusting her cardigan",
                "curling in slightly with a warm smile"
            ]
            self.moods: list[str] = ["normal", "curious", "playful", "hesitant"]
        
        def get_somatic_cue(self) -> str:
            return random.choice(self.cues)
    
    class StateManager:
        def __init__(self, data_dir: Path) -> None:
            self.state = MockState()
        
        def record_interaction(self) -> None:
            self.state.mood = random.choice(self.state.moods)


WEATHER_REACTION_PROMPT: str = """
{system_prompt}

{weather_context}
Time of day: {time_of_day}

React emotionally to this weather. 1-3 sentences, shy, somatic cues.
Stay in character. Do not just describe the weather; share how it makes you feel while you sit here with Zach.
"""


class ZahraAdapter:
    """Adapter for Zahra personality interactions."""

    FALLBACK_REACTIONS: dict[str, list[str]] = {
        "tornado": [
            "*grabs your sleeve tightly* Please... it's scary. We should go somewhere safe.",
            "*clings to you trembling* The wind is so loud... I... I want to be safe with you.",
        ],
        "storm": [
            "*flinches at a sudden flash of lightning* I... I always get a little scared of the thunder...",
            "*shrinks back slightly* The rain is really coming down. I hope the power doesn't go out...",
        ],
        "rain": [
            "*looks out the window, watching raindrops race down the pane* The sound of rain is actually kind of peaceful...",
            "*pulls her cardigan closer* A rainy day is nice for reading... if it's not too loud.",
            "*peeks at you* I... I brought an extra blanket, if you get cold."
        ],
        "sunny": [
            "*squints slightly into the light with a shy smile* It's so bright today... it makes me want to go walk in the garden.",
            "*peeks up quietly* The sun feels really warm on my face...",
            "*smiles softly* Days like this... they make me feel very warm inside."
        ],
        "cloud": [
            "*looks at the grey skies with a gentle sigh* The clouds look like soft wool blankets today...",
            "*fidgets with her hem* It's a bit gloomy... but that's okay, because I'm here with you."
        ],
        "snow": [
            "*watches the flakes fall with wide eyes* It's so pretty... everything is getting so quiet...",
            "*rubs her hands together* It's very cold... but the snow is beautiful, isn't it?"
        ],
        "fog": [
            "*looks out into the mist* It feels like we are in a little secret world today...",
            "*curls in closer* It's so foggy... everything outside has disappeared."
        ],
        "default": [
            "*looks at the sky quietly* ...the weather feels a little strange today.",
            "*peeks up quietly* ...I'm glad we are sitting here together, whatever the weather is.",
            "*fidgets with her sleeve* ...it's nice just listening to the quiet of the room."
        ]
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
            logger.debug(f"Zahra LLM unreachable, using dynamic fallback: {e}")
            weather_lower = weather_context.lower()
            
            # Find matching weather pool
            for key, reactions in self.FALLBACK_REACTIONS.items():
                if key in weather_lower:
                    return random.choice(reactions)
            return random.choice(self.FALLBACK_REACTIONS["default"])

    async def close(self) -> None:
        """Close resources."""
        await self.client.aclose()
        if hasattr(self.manager, "save_state"):
            self.manager.save_state()
