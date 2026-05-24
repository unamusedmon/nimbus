"""
Unit tests for Nimbus Companion adapters (Zahra and Morg)
"""

import pytest
from nimbus.zahra import ZahraAdapter
from nimbus.morg import MorgAdapter


@pytest.mark.asyncio
async def test_zahra_adapter_fallback() -> None:
    """Test that ZahraAdapter gracefully returns high-quality character fallbacks on LLM errors."""
    adapter = ZahraAdapter()

    # Weather contains "tornado" -> triggers tornado fallback
    reaction_tornado = await adapter.get_reaction("There is a simulated tornado warning outside.")
    assert reaction_tornado in adapter.FALLBACK_REACTIONS["tornado"]

    # Weather contains "sunny" -> triggers sunny fallback
    reaction_sunny = await adapter.get_reaction("Clear, sunny skies.")
    assert reaction_sunny in adapter.FALLBACK_REACTIONS["sunny"]

    # Verify StateManager has registered an interaction in fallback
    assert adapter.manager.state.mood in adapter.manager.state.moods
    
    await adapter.close()


@pytest.mark.asyncio
async def test_morg_adapter_fallback() -> None:
    """Test that MorgAdapter gracefully returns precise Socratic fallback commentary on LLM errors."""
    adapter = MorgAdapter()

    # Weather contains "tornado" -> triggers tornado fallback
    comment_tornado = await adapter.get_commentary("Tornado", 70.0, "Tornado")
    assert comment_tornado in adapter.FALLBACK_COMMENTARIES["tornado"]

    # Weather contains "sunny" -> triggers sunny fallback
    comment_sunny = await adapter.get_commentary("sunny", 75.0, "None")
    assert comment_sunny.format(weather_description="sunny") in [
        c.format(weather_description="sunny") for c in adapter.FALLBACK_COMMENTARIES["sunny"]
    ]

    await adapter.close()
