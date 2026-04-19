"""
Property-based tests for AI defensive spell logic using Hypothesis.
Tests Properties 9-11 from the ai-opponent design document.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hypothesis import given, settings, strategies as st, assume
from ai_controller import AIController, DifficultyConfig
from spells import SPELL_DEFS


# ---------------------------------------------------------------------------
# Mock classes (matching patterns from test_movement_properties.py)
# ---------------------------------------------------------------------------

class MockPlayer:
    """Mock Player object with minimal attributes needed for testing."""
    def __init__(self, x, y, size=40):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.hp = 100
        self.max_hp = 100
        self.mana = 100
        self.max_mana = 100
        self.spell_cooldowns = [0] * len(SPELL_DEFS)

    @property
    def center(self):
        return (int(self.x) + self.size // 2, int(self.y) + self.size // 2)


class MockProjectile:
    """Mock Projectile object with minimal attributes needed for testing."""
    def __init__(self, x, y, dx, dy, owner=None):
        self.x = float(x)
        self.y = float(y)
        self.dx = dx
        self.dy = dy
        self.owner = owner


class MockRect:
    """Mock pygame.Rect for arena boundaries."""
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.right = left + width
        self.bottom = top + height


# ---------------------------------------------------------------------------
# Shared config — deterministic, no randomness suppression
# ---------------------------------------------------------------------------

MEDIUM_CONFIG = DifficultyConfig(
    name="Medium",
    reaction_delay=400,
    cast_accuracy=1.0,
    ignore_threat_prob=0.0,
    random_spell_select=False,
)

# Defensive spell indices
SHIELD_IDX = 5
BLINK_IDX = 6
COUNTERSPELL_IDX = 7
HEAL_IDX = 8

# A large cooldown value that puts a spell firmly on cooldown
ON_COOLDOWN = 999_999_999


def make_ai(hp_ratio=1.0, mana=100, max_hp=100):
    """Helper: create a MockPlayer with given HP ratio and mana."""
    ai = MockPlayer(400, 300)
    ai.max_hp = max_hp
    ai.hp = hp_ratio * max_hp
    ai.mana = mana
    ai.max_mana = 100
    # All spells off cooldown by default
    ai.spell_cooldowns = [0] * len(SPELL_DEFS)
    return ai


def make_threat():
    """Helper: create a single threat projectile heading toward (420, 320)."""
    return MockProjectile(x=100, y=100, dx=5, dy=5)


# ---------------------------------------------------------------------------
# Property 9: Defensive spell priority ordering
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 9: Defensive spell priority ordering
@given(
    hp_ratio=st.floats(min_value=0.01, max_value=0.99),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=200)
def test_property9a_single_threat_shield_probability(hp_ratio, now):
    """
    **Validates: Requirements 5.1, 5.2, 5.4**

    Sub-case (a): With a single threat and Shield available, _should_cast_defensive
    returns Shield (index 5) with probability approximately (1 - hp_ratio).
    Tested statistically over many trials.
    """
    # Feature: ai-opponent, Property 9: Defensive spell priority ordering
    ai = make_ai(hp_ratio=hp_ratio, mana=100)
    # Shield available, Counterspell on cooldown (so Shield is the top candidate)
    ai.spell_cooldowns[COUNTERSPELL_IDX] = ON_COOLDOWN
    ai.spell_cooldowns[BLINK_IDX] = ON_COOLDOWN

    human = MockPlayer(200, 200)
    threats = [make_threat()]

    controller = AIController(ai, MEDIUM_CONFIG)

    # Run many trials to estimate the empirical cast rate
    N = 500
    shield_casts = 0
    for _ in range(N):
        result = controller._should_cast_defensive(human, threats, now)
        if result == SHIELD_IDX:
            shield_casts += 1

    empirical_rate = shield_casts / N
    expected_rate = 1.0 - hp_ratio

    # Allow ±0.08 tolerance for statistical noise at N=500
    tolerance = 0.08
    assert abs(empirical_rate - expected_rate) <= tolerance, (
        f"Shield cast rate {empirical_rate:.3f} deviates from expected "
        f"{expected_rate:.3f} (hp_ratio={hp_ratio:.3f}, tolerance=±{tolerance})"
    )


# Feature: ai-opponent, Property 9: Defensive spell priority ordering
@given(
    hp_ratio=st.floats(min_value=0.31, max_value=0.99),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property9b_multiple_threats_counterspell(hp_ratio, now):
    """
    **Validates: Requirements 5.1, 5.2, 5.4**

    Sub-case (b): With two or more simultaneous threats and Counterspell available,
    _should_cast_defensive shall return Counterspell (index 7).
    """
    # Feature: ai-opponent, Property 9: Defensive spell priority ordering
    ai = make_ai(hp_ratio=hp_ratio, mana=100)
    # All defensive spells off cooldown
    ai.spell_cooldowns = [0] * len(SPELL_DEFS)

    human = MockPlayer(200, 200)
    threats = [make_threat(), make_threat()]  # Two simultaneous threats

    controller = AIController(ai, MEDIUM_CONFIG)
    result = controller._should_cast_defensive(human, threats, now)

    assert result == COUNTERSPELL_IDX, (
        f"Expected Counterspell (index {COUNTERSPELL_IDX}) with 2 threats, "
        f"got {result} (hp_ratio={hp_ratio:.3f})"
    )


# Feature: ai-opponent, Property 9: Defensive spell priority ordering
@given(
    hp_ratio=st.floats(min_value=0.31, max_value=0.99),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property9c_threat_blink_fallback(hp_ratio, now):
    """
    **Validates: Requirements 5.1, 5.2, 5.4**

    Sub-case (c): With a threat present and both Shield (5) and Counterspell (7)
    unavailable, but Blink (6) available, _should_cast_defensive shall return
    Blink (index 6).
    """
    # Feature: ai-opponent, Property 9: Defensive spell priority ordering
    ai = make_ai(hp_ratio=hp_ratio, mana=100)
    # Shield and Counterspell on cooldown; Blink available
    ai.spell_cooldowns[SHIELD_IDX] = ON_COOLDOWN
    ai.spell_cooldowns[COUNTERSPELL_IDX] = ON_COOLDOWN
    ai.spell_cooldowns[BLINK_IDX] = 0

    human = MockPlayer(200, 200)
    threats = [make_threat()]

    controller = AIController(ai, MEDIUM_CONFIG)
    result = controller._should_cast_defensive(human, threats, now)

    assert result == BLINK_IDX, (
        f"Expected Blink (index {BLINK_IDX}) when Shield/Counterspell unavailable, "
        f"got {result} (hp_ratio={hp_ratio:.3f})"
    )


# ---------------------------------------------------------------------------
# Property 10: Heal at critical HP
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 10: Heal at critical HP
@given(
    hp_ratio=st.floats(min_value=0.01, max_value=0.2999),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property10_heal_at_critical_hp(hp_ratio, now):
    """
    **Validates: Requirements 5.3**

    For any game state where the AI wizard's HP is below 30% of max HP,
    Heal (index 8) is not on cooldown, and no threats are detected,
    _should_cast_defensive shall return the Heal spell index (8).
    Uses mana >= 35 to ensure Heal is affordable.
    """
    # Feature: ai-opponent, Property 10: Heal at critical HP
    ai = make_ai(hp_ratio=hp_ratio, mana=100)
    # Heal off cooldown; other defensive spells on cooldown to isolate Heal path
    ai.spell_cooldowns[HEAL_IDX] = 0
    ai.spell_cooldowns[SHIELD_IDX] = ON_COOLDOWN
    ai.spell_cooldowns[BLINK_IDX] = ON_COOLDOWN
    ai.spell_cooldowns[COUNTERSPELL_IDX] = ON_COOLDOWN

    human = MockPlayer(200, 200)
    threats = []  # No threats

    controller = AIController(ai, MEDIUM_CONFIG)
    result = controller._should_cast_defensive(human, threats, now)

    assert result == HEAL_IDX, (
        f"Expected Heal (index {HEAL_IDX}) at critical HP (hp_ratio={hp_ratio:.3f}), "
        f"got {result}"
    )


# ---------------------------------------------------------------------------
# Property 11: Low mana suppresses defensive casting (with Heal exception)
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 11: Low mana suppresses defensive casting (with Heal exception)
@given(
    mana=st.floats(min_value=0.0, max_value=29.99),
    hp_ratio=st.floats(min_value=0.15, max_value=1.0),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property11a_low_mana_high_hp_returns_none(mana, hp_ratio, now):
    """
    **Validates: Requirements 5.5**

    Sub-case (a): When mana is in [0, 29] and HP >= 15%,
    _should_cast_defensive shall return None.
    """
    # Feature: ai-opponent, Property 11: Low mana suppresses defensive casting (with Heal exception)
    ai = make_ai(hp_ratio=hp_ratio, mana=mana)
    # All defensive spells off cooldown — only mana suppression should block them
    ai.spell_cooldowns = [0] * len(SPELL_DEFS)

    human = MockPlayer(200, 200)
    # Use a threat to exercise the full priority tree
    threats = [make_threat()]

    controller = AIController(ai, MEDIUM_CONFIG)
    result = controller._should_cast_defensive(human, threats, now)

    assert result is None, (
        f"Expected None when mana={mana:.2f} (< 30) and hp_ratio={hp_ratio:.3f} (>= 15%), "
        f"got {result}"
    )


# Feature: ai-opponent, Property 11: Low mana suppresses defensive casting (with Heal exception)
@given(
    mana=st.floats(min_value=0.0, max_value=29.99),
    hp_ratio=st.floats(min_value=0.001, max_value=0.1499),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property11b_low_mana_critical_hp_heal_or_none(mana, hp_ratio, now):
    """
    **Validates: Requirements 5.5**

    Sub-case (b): When mana is in [0, 29] and HP < 15%,
    _should_cast_defensive shall return either Heal (8) or None.
    No other defensive spell index is permitted.

    Note: Heal costs 35 mana. Since mana < 30 < 35, Heal is always unaffordable
    here, so the result will always be None. The test verifies that no other
    defensive spell is returned (i.e., the result is None or 8 only).
    """
    # Feature: ai-opponent, Property 11: Low mana suppresses defensive casting (with Heal exception)
    ai = make_ai(hp_ratio=hp_ratio, mana=mana)
    # All defensive spells off cooldown
    ai.spell_cooldowns = [0] * len(SPELL_DEFS)

    human = MockPlayer(200, 200)
    threats = [make_threat()]

    controller = AIController(ai, MEDIUM_CONFIG)
    result = controller._should_cast_defensive(human, threats, now)

    assert result is None or result == HEAL_IDX, (
        f"Expected None or Heal (index {HEAL_IDX}) when mana={mana:.2f} (< 30) "
        f"and hp_ratio={hp_ratio:.3f} (< 15%), got {result}"
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
