import os
import sys
import unittest

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from arena import Arena, Building, projectile_hits_obstacle, resolve_actor_move
from spells import SPELL_DEFS, create_summon_effect


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


class TestTerrainAndBuildings(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_actor_movement_stops_at_building(self):
        arena_rect = pygame.Rect(0, 0, 400, 300)
        actor = pygame.Rect(80, 120, 40, 40)
        obstacle = pygame.Rect(140, 80, 60, 120)

        moved = resolve_actor_move(actor, 80, 0, arena_rect, [obstacle])
        self.assertEqual(moved.right, obstacle.left)

    def test_projectile_hit_detects_obstacle(self):
        obstacle = pygame.Rect(140, 120, 40, 40)
        hit = projectile_hits_obstacle(150, 130, 6, [obstacle])
        self.assertEqual(hit, obstacle)

    def test_building_takes_damage_and_is_removed(self):
        arena = Arena(960, 620, margin=60, left_margin=160, right_margin=160)
        building = Building(rect=pygame.Rect(300, 250, 60, 60), hp=10, max_hp=10)
        arena.buildings = [building]

        arena.damage_building_at(building.rect, 12)
        arena.prune_destroyed()
        self.assertEqual(len(arena.buildings), 0)

    def test_summon_spawns_outside_blocked_rect(self):
        arena = Arena(960, 620, margin=60, left_margin=160, right_margin=160)
        owner = MockPlayer(280, 240)
        target = MockPlayer(600, 300)
        # Force the default summon spawn point to collide with this blocker.
        blocker = pygame.Rect(int(owner.center[0] - 40), int(owner.center[1] - 40), 90, 90)
        arena.buildings = [Building(rect=blocker, hp=30, max_hp=30)]

        summon = create_summon_effect(owner, target, _spell_by_name("Minotaur"), arena.rect, arena=arena)
        summon_rect = pygame.Rect(int(summon.x), int(summon.y), summon.size, summon.size)
        self.assertFalse(summon_rect.colliderect(blocker))


if __name__ == "__main__":
    unittest.main()
