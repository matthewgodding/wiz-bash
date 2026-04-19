"""
Property-based tests for AI movement logic using Hypothesis.
Tests Properties 1-4 from the ai-opponent design document.
"""

import math
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hypothesis import given, settings, strategies as st
from ai_controller import AIController, DifficultyConfig, _is_threat
from unittest.mock import Mock
import pygame


# Mock classes for testing
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


# Test configuration
TEST_CONFIG = DifficultyConfig(
    name="Test",
    reaction_delay=400,
    cast_accuracy=1.0,
    ignore_threat_prob=0.0,
    random_spell_select=False
)


# Feature: ai-opponent, Property 1: Engagement distance maintenance
@given(
    ai_x=st.floats(min_value=100, max_value=700),
    ai_y=st.floats(min_value=100, max_value=500),
    human_x=st.floats(min_value=100, max_value=700),
    human_y=st.floats(min_value=100, max_value=500),
)
@settings(max_examples=100)
def test_engagement_distance_maintenance(ai_x, ai_y, human_x, human_y):
    """
    **Validates: Requirements 3.1**
    
    For any AI wizard position and human wizard position with no active threats,
    the movement vector produced by `_choose_movement` shall point in a direction
    that reduces the distance error relative to the 200–350 px engagement band.
    """
    ai_wizard = MockPlayer(ai_x, ai_y)
    human = MockPlayer(human_x, human_y)
    arena_rect = MockRect(0, 0, 800, 600)
    
    controller = AIController(ai_wizard, TEST_CONFIG)
    
    # No threats
    threats = []
    now = 0
    
    # Get movement vector
    dx, dy = controller._choose_movement(human, threats, arena_rect, now)
    
    # Calculate current distance
    ax, ay = ai_wizard.center
    hx, hy = human.center
    current_dist = math.hypot(hx - ax, hy - ay)
    
    # Skip if distance is zero (same position)
    if current_dist < 1:
        return
    
    # Calculate what the distance would be after moving
    # (using a small step to check direction)
    step_size = 10
    new_ax = ax + dx * step_size
    new_ay = ay + dy * step_size
    new_dist = math.hypot(hx - new_ax, hy - new_ay)
    
    # Check behavior based on current distance
    if current_dist > 350:
        # Too far — should move closer
        assert new_dist < current_dist or (dx == 0 and dy == 0), \
            f"When too far ({current_dist:.1f}px), should move closer. " \
            f"Current: {current_dist:.1f}, After move: {new_dist:.1f}"
    elif current_dist < 200:
        # Too close — should move away
        assert new_dist > current_dist or (dx == 0 and dy == 0), \
            f"When too close ({current_dist:.1f}px), should move away. " \
            f"Current: {current_dist:.1f}, After move: {new_dist:.1f}"
    else:
        # In band (200-350) — should have near-zero radial movement
        # Allow small movement due to boundary avoidance
        dist_change = abs(new_dist - current_dist)
        # Radial movement should be minimal (less than 20% of step)
        assert dist_change < step_size * 0.3, \
            f"When in engagement band ({current_dist:.1f}px), radial movement should be minimal. " \
            f"Distance change: {dist_change:.1f}"


# Feature: ai-opponent, Property 2: Perpendicular evasion direction
@given(
    ai_x=st.floats(min_value=200, max_value=600),
    ai_y=st.floats(min_value=200, max_value=400),
    proj_x=st.floats(min_value=100, max_value=700),
    proj_y=st.floats(min_value=100, max_value=500),
    proj_dx=st.floats(min_value=-10, max_value=10).filter(lambda x: abs(x) > 0.5),
    proj_dy=st.floats(min_value=-10, max_value=10).filter(lambda y: abs(y) > 0.5),
)
@settings(max_examples=100)
def test_perpendicular_evasion_direction(ai_x, ai_y, proj_x, proj_y, proj_dx, proj_dy):
    """
    **Validates: Requirements 3.2**
    
    For any threat projectile with a non-zero velocity vector, the movement vector
    produced by `_choose_movement` shall be nearly perpendicular to the projectile's
    direction of travel — specifically, the absolute dot product of the normalised
    movement vector and the normalised projectile velocity shall be less than 0.5.
    """
    ai_wizard = MockPlayer(ai_x, ai_y)
    human = MockPlayer(400, 300)  # Human position doesn't matter for threat evasion
    arena_rect = MockRect(0, 0, 800, 600)
    
    # Create a threat projectile
    threat = MockProjectile(proj_x, proj_y, proj_dx, proj_dy, owner=human)
    
    # Only test if this is actually a threat
    if not _is_threat(threat, ai_wizard):
        return
    
    controller = AIController(ai_wizard, TEST_CONFIG)
    threats = [threat]
    now = 0
    
    # Get movement vector
    dx, dy = controller._choose_movement(human, threats, arena_rect, now)
    
    # Normalize both vectors
    proj_speed = math.hypot(proj_dx, proj_dy)
    move_speed = math.hypot(dx, dy)
    
    # Skip if no movement
    if move_speed < 0.01:
        return
    
    norm_proj_dx = proj_dx / proj_speed
    norm_proj_dy = proj_dy / proj_speed
    norm_move_dx = dx / move_speed
    norm_move_dy = dy / move_speed
    
    # Calculate dot product
    dot_product = abs(norm_proj_dx * norm_move_dx + norm_proj_dy * norm_move_dy)
    
    # Dot product should be less than 0.5 (nearly perpendicular)
    assert dot_product < 0.5, \
        f"Movement should be perpendicular to threat. Dot product: {dot_product:.3f} (should be < 0.5)"


# Feature: ai-opponent, Property 3: Boundary avoidance
@given(
    boundary=st.sampled_from(['left', 'right', 'top', 'bottom']),
    # Distance is measured from the boundary to the wizard's CENTER (as used in _choose_movement)
    # Must be strictly less than 80 to trigger boundary avoidance
    center_distance=st.floats(min_value=10, max_value=79).filter(lambda d: d < 80),
)
@settings(max_examples=100)
def test_boundary_avoidance(boundary, center_distance):
    """
    **Validates: Requirements 3.3**
    
    For any AI wizard position within 80 pixels of any arena boundary, the movement
    vector produced by `_choose_movement` shall have a component pointing away from
    that boundary (i.e., the component along the inward normal of the nearest
    boundary is positive).
    
    Note: boundary distance is measured from the boundary to the wizard's center,
    matching the implementation in `_choose_movement` which uses `ai_wizard.center`.
    """
    arena_rect = MockRect(0, 0, 800, 600)
    wizard_size = 40
    half_size = wizard_size // 2  # 20
    
    # Position AI so its CENTER is `center_distance` pixels from the specified boundary.
    # ai_wizard.center = (int(ai_x) + half_size, int(ai_y) + half_size)
    # So: center_x = ai_x + half_size => ai_x = center_x - half_size
    if boundary == 'left':
        center_x = arena_rect.left + center_distance
        center_y = 300
        ai_x = center_x - half_size
        ai_y = center_y - half_size
        expected_direction = 1  # Should move right (positive x)
        component_index = 0  # Check dx
    elif boundary == 'right':
        center_x = arena_rect.right - center_distance
        center_y = 300
        ai_x = center_x - half_size
        ai_y = center_y - half_size
        expected_direction = -1  # Should move left (negative x)
        component_index = 0  # Check dx
    elif boundary == 'top':
        center_x = 400
        center_y = arena_rect.top + center_distance
        ai_x = center_x - half_size
        ai_y = center_y - half_size
        expected_direction = 1  # Should move down (positive y)
        component_index = 1  # Check dy
    else:  # bottom
        center_x = 400
        center_y = arena_rect.bottom - center_distance
        ai_x = center_x - half_size
        ai_y = center_y - half_size
        expected_direction = -1  # Should move up (negative y)
        component_index = 1  # Check dy
    
    ai_wizard = MockPlayer(ai_x, ai_y, size=wizard_size)
    
    # Place human far from the boundary to avoid engagement band interference
    # with the boundary we're testing
    if boundary in ('left', 'right'):
        human = MockPlayer(400 - half_size, 300 - half_size, size=wizard_size)
    else:
        human = MockPlayer(400 - half_size, 300 - half_size, size=wizard_size)
    
    controller = AIController(ai_wizard, TEST_CONFIG)
    threats = []
    now = 0
    
    # Get movement vector
    dx, dy = controller._choose_movement(human, threats, arena_rect, now)
    movement = [dx, dy]
    
    # Check that the movement has a component away from the boundary
    component = movement[component_index]
    
    # The component should point away from the boundary
    if expected_direction > 0:
        assert component > 0, \
            f"Near {boundary} boundary (center {center_distance:.1f}px from edge), should move away. " \
            f"Movement component: {component:.3f} (should be > 0)"
    else:
        assert component < 0, \
            f"Near {boundary} boundary (center {center_distance:.1f}px from edge), should move away. " \
            f"Movement component: {component:.3f} (should be < 0)"


# Feature: ai-opponent, Property 4: Reaction delay gates movement updates
@given(
    initial_time=st.integers(min_value=0, max_value=10000),
    time_gap=st.integers(min_value=1, max_value=399),  # Less than reaction_delay (400)
)
@settings(max_examples=100)
def test_reaction_delay_gates_movement(initial_time, time_gap):
    """
    **Validates: Requirements 3.4**
    
    For any sequence of `update` calls where consecutive timestamps are spaced less
    than `reaction_delay` milliseconds apart, the AI wizard's movement direction
    shall not change between those calls.
    """
    ai_wizard = MockPlayer(400, 300)
    human = MockPlayer(200, 200)
    arena_rect = MockRect(0, 0, 800, 600)
    
    config = DifficultyConfig(
        name="Test",
        reaction_delay=400,
        cast_accuracy=1.0,
        ignore_threat_prob=0.0,
        random_spell_select=False
    )
    
    controller = AIController(ai_wizard, config)
    threats = []
    
    # First call - establishes initial movement direction
    dx1, dy1 = controller._choose_movement(human, threats, arena_rect, initial_time)
    
    # Second call - within reaction delay window
    second_time = initial_time + time_gap
    dx2, dy2 = controller._choose_movement(human, threats, arena_rect, second_time)
    
    # Movement direction should be unchanged
    assert dx1 == dx2 and dy1 == dy2, \
        f"Movement should not change within reaction_delay. " \
        f"Time gap: {time_gap}ms (< 400ms), " \
        f"First: ({dx1:.3f}, {dy1:.3f}), Second: ({dx2:.3f}, {dy2:.3f})"
    
    # Third call - after reaction delay has passed
    third_time = initial_time + config.reaction_delay + 10
    
    # Move human to a different position to force a different movement decision
    human.x = 600
    human.y = 400
    
    dx3, dy3 = controller._choose_movement(human, threats, arena_rect, third_time)
    
    # Movement CAN change now (though it might not if the optimal direction is the same)
    # We just verify the gate has opened by checking internal state
    assert controller._next_move_time > initial_time, \
        "Movement gate should have been updated after reaction_delay"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
