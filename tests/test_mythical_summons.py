"""
Unit tests for mythical summon spell behavior.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from spells import SPELL_DEFS, create_summon_effect, SummonedCreature, OneShotSummon


class MockRect:
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.right = left + width
        self.bottom = top + height


class MockPlayer:
    def __init__(self, x=200, y=200, size=40):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.hp = 100
        self.max_hp = 100
        self.mana = 100
        self.max_mana = 100
        self.color = (100, 120, 180)
        self.shield = 0
        self.slow_timer = 0

    @property
    def center(self):
        return (self.x + self.size / 2, self.y + self.size / 2)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def is_alive(self):
        return self.hp > 0


def _spell_by_name(name):
    return next(spell for spell in SPELL_DEFS if spell["name"] == name)


class TestMythicalSummons(unittest.TestCase):
    def test_create_one_shot_phoenix(self):
        owner = MockPlayer(100, 100)
        target = MockPlayer(400, 300)
        arena = MockRect(0, 0, 800, 600)
        phoenix = create_summon_effect(owner, target, _spell_by_name("Phoenix Dive"), arena)
        self.assertIsInstance(phoenix, OneShotSummon)

    def test_one_shot_damages_target_and_expires(self):
        owner = MockPlayer(100, 100)
        target = MockPlayer(400, 300)
        arena = MockRect(0, 0, 800, 600)
        phoenix_spell = _spell_by_name("Phoenix Dive")
        phoenix = create_summon_effect(owner, target, phoenix_spell, arena)
        hp_before = target.hp
        phoenix.update(16, arena, target, [], [])
        self.assertLess(target.hp, hp_before)
        phoenix.update(300, arena, target, [], [])
        self.assertFalse(phoenix.alive)

    def test_create_temporary_summon_and_expire(self):
        owner = MockPlayer(100, 100)
        target = MockPlayer(400, 300)
        arena = MockRect(0, 0, 800, 600)
        minotaur = create_summon_effect(owner, target, _spell_by_name("Minotaur"), arena)
        self.assertIsInstance(minotaur, SummonedCreature)
        minotaur.update(minotaur.lifetime_ms + 1, arena, target, [], [])
        self.assertFalse(minotaur.alive)

    def test_summon_tracks_owner_liveness(self):
        owner = MockPlayer(100, 100)
        target = MockPlayer(400, 300)
        arena = MockRect(0, 0, 800, 600)
        griffin = create_summon_effect(owner, target, _spell_by_name("Griffin"), arena)
        owner.hp = 0
        griffin.update(16, arena, target, [], [])
        self.assertFalse(griffin.alive)


if __name__ == "__main__":
    unittest.main()
