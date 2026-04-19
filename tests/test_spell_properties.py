"""
Property-based tests for AI spell selection logic using Hypothesis.
Tests Properties 5-8 from the ai-opponent design document.
"""

import math
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hypothesis import given, settings, strategies as st, assume
from ai_controller import AIController, DifficultyConfig, _lead_target
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
# Shared test config — cast_accuracy=1.0 ensures spell is always chosen
# ---------------------------------------------------------------------------

MEDIUM_CONFIG = DifficultyConfig(
    name="Medium",
    reaction_delay=400,
    cast_accuracy=1.0,
    ignore_threat_prob=0.0,
    random_spell_select=False,
)

# Offensive spell indices (0-4) and their mana costs
OFFENSIVE_INDICES = list(range(5))
OFFENSIVE_MANA_COSTS = [SPELL_DEFS[i]["mana"] for i in OFFENSIVE_INDICES]
MIN_OFFENSIVE_MANA = min(OFFENSIVE_MANA_COSTS)  # 10 (Arcane Missile)


# ---------------------------------------------------------------------------
# Property 5: Offensive spell is always available and within mana
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 5: Offensive spell is always available and within mana
@given(
    ai_mana=st.floats(min_value=20.0, max_value=100.0),
    # Which offensive spells are NOT on cooldown (at least one must be True)
    available_mask=st.lists(st.booleans(), min_size=5, max_size=5).filter(any),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property5_offensive_spell_available_and_within_mana(ai_mana, available_mask, now):
    """
    **Validates: Requirements 4.1, 4.3**

    For any game state where the AI wizard's mana is >= 20 and at least one
    offensive spell is not on cooldown, _choose_spell shall return an index
    corresponding to an offensive spell that is not on cooldown and whose mana
    cost does not exceed the AI wizard's current mana.
    """
    ai_wizard = MockPlayer(400, 300)
    ai_wizard.mana = ai_mana

    # Set cooldowns so that available_mask[i] == True means spell i is ready
    for i in OFFENSIVE_INDICES:
        if available_mask[i]:
            # Off cooldown: last cast was long ago
            ai_wizard.spell_cooldowns[i] = 0
        else:
            # On cooldown: last cast was just now
            ai_wizard.spell_cooldowns[i] = now

    # Ensure at least one available spell is also affordable
    affordable_available = [
        i for i in OFFENSIVE_INDICES
        if available_mask[i] and SPELL_DEFS[i]["mana"] <= ai_mana
    ]
    assume(len(affordable_available) > 0)

    human = MockPlayer(200, 200)
    human.hp = 60
    human.max_hp = 100

    controller = AIController(ai_wizard, MEDIUM_CONFIG)
    result = controller._choose_spell(human, now)

    assert result is not None, (
        f"Expected a spell index but got None. mana={ai_mana}, "
        f"available_mask={available_mask}"
    )
    assert result in OFFENSIVE_INDICES, (
        f"Returned index {result} is not an offensive spell (0-4)"
    )

    spell = SPELL_DEFS[result]
    assert spell["mana"] <= ai_mana, (
        f"Chosen spell '{spell['name']}' costs {spell['mana']} mana but AI only has {ai_mana}"
    )

    cooldown_elapsed = (now - ai_wizard.spell_cooldowns[result]) >= spell["cooldown"]
    assert cooldown_elapsed, (
        f"Chosen spell '{spell['name']}' is still on cooldown"
    )


# ---------------------------------------------------------------------------
# Property 6: Spell preference follows game state
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 6: Spell preference follows game state
@given(
    human_hp_ratio=st.floats(min_value=0.51, max_value=1.0),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property6_prefers_highest_damage_when_human_hp_above_50(human_hp_ratio, now):
    """
    **Validates: Requirements 4.2**

    For any game state where the human wizard's HP is above 50% and multiple
    offensive spells are available, _choose_spell (on non-Easy difficulty) shall
    return the spell with the highest damage value among available offensive spells.
    """
    ai_wizard = MockPlayer(400, 300)
    ai_wizard.mana = 100.0  # Enough for all spells

    # All offensive spells off cooldown
    for i in OFFENSIVE_INDICES:
        ai_wizard.spell_cooldowns[i] = 0

    human = MockPlayer(200, 200)
    human.max_hp = 100
    human.hp = human_hp_ratio * human.max_hp

    controller = AIController(ai_wizard, MEDIUM_CONFIG)

    # Simulate human standing still (no velocity) so speed branch is not taken
    # Set _prev_human_pos to same as current center to produce zero velocity
    controller._prev_human_pos = human.center
    controller._prev_human_time = now - 100  # 100ms ago, same position => vel=(0,0)

    result = controller._choose_spell(human, now)

    assert result is not None, "Expected a spell index but got None"
    assert result in OFFENSIVE_INDICES

    # Determine which spells are available (off cooldown and affordable)
    available = [
        i for i in OFFENSIVE_INDICES
        if (now - ai_wizard.spell_cooldowns[i]) >= SPELL_DEFS[i]["cooldown"]
        and SPELL_DEFS[i]["mana"] <= ai_wizard.mana
    ]
    best_damage = max(SPELL_DEFS[i]["damage"] for i in available)
    assert SPELL_DEFS[result]["damage"] == best_damage, (
        f"Expected highest-damage spell (damage={best_damage}) but got "
        f"'{SPELL_DEFS[result]['name']}' (damage={SPELL_DEFS[result]['damage']})"
    )


# Feature: ai-opponent, Property 6 (fast-human branch): Spell preference follows game state
@given(
    human_speed=st.floats(min_value=3.01, max_value=20.0),
    now=st.integers(min_value=10000, max_value=100000),
)
@settings(max_examples=100)
def test_property6_prefers_fastest_spell_when_human_moving_fast(human_speed, now):
    """
    **Validates: Requirements 4.2**

    For any game state where the human wizard is moving at speed > 3 px/frame,
    _choose_spell shall return the spell with the highest projectile speed among
    available offensive spells.
    """
    ai_wizard = MockPlayer(400, 300)
    ai_wizard.mana = 100.0

    for i in OFFENSIVE_INDICES:
        ai_wizard.spell_cooldowns[i] = 0

    human = MockPlayer(200, 200)
    human.hp = 60
    human.max_hp = 100

    controller = AIController(ai_wizard, MEDIUM_CONFIG)

    # Simulate human moving horizontally at human_speed px/ms * dt
    # _choose_spell computes: human_vel = (hx - px) / dt, (hy - py) / dt
    # We want math.hypot(vx, vy) > 3
    # Use dt=1 ms so displacement == speed in px/ms
    dt = 1
    prev_cx, prev_cy = human.center
    # Move human so that velocity estimate = human_speed in x direction
    human.x += human_speed * dt
    controller._prev_human_pos = (prev_cx, prev_cy)
    controller._prev_human_time = now - dt

    result = controller._choose_spell(human, now)

    assert result is not None, "Expected a spell index but got None"
    assert result in OFFENSIVE_INDICES

    available = [
        i for i in OFFENSIVE_INDICES
        if (now - ai_wizard.spell_cooldowns[i]) >= SPELL_DEFS[i]["cooldown"]
        and SPELL_DEFS[i]["mana"] <= ai_wizard.mana
    ]
    best_speed = max(SPELL_DEFS[i]["speed"] for i in available)
    assert SPELL_DEFS[result]["speed"] == best_speed, (
        f"Expected fastest spell (speed={best_speed}) but got "
        f"'{SPELL_DEFS[result]['name']}' (speed={SPELL_DEFS[result]['speed']})"
    )


# ---------------------------------------------------------------------------
# Property 7: Lead-aim point is ahead of the human
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 7: Lead-aim point is ahead of the human
@given(
    ai_x=st.floats(min_value=50, max_value=750),
    ai_y=st.floats(min_value=50, max_value=550),
    human_x=st.floats(min_value=50, max_value=750),
    human_y=st.floats(min_value=50, max_value=550),
    vx=st.floats(min_value=-15, max_value=15),
    vy=st.floats(min_value=-15, max_value=15),
    spell_speed=st.floats(min_value=0.1, max_value=30.0),
)
@settings(max_examples=100)
def test_property7_lead_aim_point_is_ahead_of_human(
    ai_x, ai_y, human_x, human_y, vx, vy, spell_speed
):
    """
    **Validates: Requirements 4.4**

    For any human wizard position, velocity vector, and spell speed > 0,
    _lead_target shall return a point that is displaced from the human's current
    centre in the direction of the human's velocity — specifically, the dot product
    of (lead_point - human_centre) and the human's velocity vector shall be
    non-negative.
    """
    # Skip the zero-velocity case (lead point equals current position, dot product = 0)
    assume(abs(vx) > 1e-6 or abs(vy) > 1e-6)

    ai_wizard = MockPlayer(ai_x, ai_y)
    human = MockPlayer(human_x, human_y)

    lead_x, lead_y = _lead_target(ai_wizard, human, spell_speed, (vx, vy))

    hx, hy = human.center
    # Displacement from human centre to lead point
    disp_x = lead_x - hx
    disp_y = lead_y - hy

    # Dot product with velocity vector
    dot = disp_x * vx + disp_y * vy

    assert dot >= 0, (
        f"Lead point ({lead_x:.2f}, {lead_y:.2f}) is not ahead of human "
        f"centre ({hx}, {hy}) given velocity ({vx:.2f}, {vy:.2f}). "
        f"Dot product: {dot:.4f} (should be >= 0)"
    )


# ---------------------------------------------------------------------------
# Property 8: Low mana suppresses offensive casting
# ---------------------------------------------------------------------------

# Feature: ai-opponent, Property 8: Low mana suppresses offensive casting
@given(
    ai_mana=st.floats(min_value=0.0, max_value=19.99),
    now=st.integers(min_value=0, max_value=100000),
)
@settings(max_examples=100)
def test_property8_low_mana_suppresses_offensive_casting(ai_mana, now):
    """
    **Validates: Requirements 4.5**

    For any game state where the AI wizard's mana is in the range [0, 19],
    _choose_spell shall return None (no offensive spell is cast).
    """
    ai_wizard = MockPlayer(400, 300)
    ai_wizard.mana = ai_mana

    # All spells off cooldown so the only reason to return None is low mana
    for i in OFFENSIVE_INDICES:
        ai_wizard.spell_cooldowns[i] = 0

    human = MockPlayer(200, 200)
    human.hp = 60
    human.max_hp = 100

    controller = AIController(ai_wizard, MEDIUM_CONFIG)
    result = controller._choose_spell(human, now)

    assert result is None, (
        f"Expected None when mana={ai_mana:.2f} (< 20) but got spell index {result} "
        f"('{SPELL_DEFS[result]['name']}')"
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
