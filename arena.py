import random
from dataclasses import dataclass

import pygame

ARENA_COLOR = (40, 40, 60)
BORDER_COLOR = (100, 100, 140)
FLOOR_COLOR = (55, 55, 75)
TERRAIN_DOT_COLOR = (70, 72, 96)
BUILDING_COLOR = (120, 108, 92)
BUILDING_BORDER = (70, 62, 54)
BUILDING_DESTROYED_COLOR = (66, 62, 60)


@dataclass
class Building:
    rect: pygame.Rect
    hp: float
    max_hp: float
    kind: str = "stone"

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0.0, self.hp - float(amount))


def resolve_actor_move(rect, dx, dy, arena_rect, obstacles):
    moved = rect.copy()
    moved.x += int(round(dx))
    for obstacle in obstacles:
        if moved.colliderect(obstacle):
            if dx > 0:
                moved.right = obstacle.left
            elif dx < 0:
                moved.left = obstacle.right
    moved.left = max(arena_rect.left, moved.left)
    moved.right = min(arena_rect.right, moved.right)

    moved.y += int(round(dy))
    for obstacle in obstacles:
        if moved.colliderect(obstacle):
            if dy > 0:
                moved.bottom = obstacle.top
            elif dy < 0:
                moved.top = obstacle.bottom
    moved.top = max(arena_rect.top, moved.top)
    moved.bottom = min(arena_rect.bottom, moved.bottom)
    return moved


def rect_collides_obstacles(rect, obstacles):
    return any(rect.colliderect(obs) for obs in obstacles)


def projectile_hits_obstacle(x, y, radius, obstacles):
    probe = pygame.Rect(int(x - radius), int(y - radius), int(radius * 2), int(radius * 2))
    for obstacle in obstacles:
        if probe.colliderect(obstacle):
            return obstacle
    return None


class Arena:
    def __init__(self, screen_w, screen_h, margin=60, left_margin=None, right_margin=None):
        lm = left_margin  if left_margin  is not None else margin
        rm = right_margin if right_margin is not None else margin
        self.rect = pygame.Rect(lm, margin, screen_w - lm - rm, screen_h - margin * 2)
        self.buildings = []

    def reset_random_terrain(self, spawn_points):
        self.buildings = []
        target_count = random.randint(6, 10)
        spawn_bubbles = [pygame.Rect(int(x - 85), int(y - 85), 170, 170) for x, y in spawn_points]
        attempts = 0
        while len(self.buildings) < target_count and attempts < 240:
            attempts += 1
            w = random.randint(48, 96)
            h = random.randint(40, 92)
            x = random.randint(self.rect.left + 20, self.rect.right - w - 20)
            y = random.randint(self.rect.top + 20, self.rect.bottom - h - 20)
            candidate = pygame.Rect(x, y, w, h)

            if any(candidate.colliderect(bubble) for bubble in spawn_bubbles):
                continue
            if any(candidate.inflate(26, 26).colliderect(b.rect) for b in self.buildings if b.alive):
                continue
            hp = random.randint(24, 56)
            self.buildings.append(Building(rect=candidate, hp=hp, max_hp=hp))

    def get_blocking_rects(self):
        return [b.rect for b in self.buildings if b.alive]

    def is_spawn_valid(self, rect):
        if not self.rect.contains(rect):
            return False
        return not rect_collides_obstacles(rect, self.get_blocking_rects())

    def damage_building_at(self, obstacle_rect, amount):
        for building in self.buildings:
            if building.alive and building.rect == obstacle_rect:
                building.take_damage(amount)
                return building
        return None

    def prune_destroyed(self):
        self.buildings = [b for b in self.buildings if b.alive]

    def draw(self, surface):
        # Floor
        pygame.draw.rect(surface, FLOOR_COLOR, self.rect)
        for x in range(self.rect.left + 10, self.rect.right, 22):
            for y in range(self.rect.top + 10, self.rect.bottom, 22):
                if (x + y) % 44 == 0:
                    surface.set_at((x, y), TERRAIN_DOT_COLOR)

        for building in self.buildings:
            col = BUILDING_COLOR if building.alive else BUILDING_DESTROYED_COLOR
            pygame.draw.rect(surface, col, building.rect, border_radius=3)
            pygame.draw.rect(surface, BUILDING_BORDER, building.rect, 2, border_radius=3)
            if building.alive:
                hp_ratio = 0 if building.max_hp <= 0 else building.hp / building.max_hp
                bar_bg = pygame.Rect(building.rect.left, building.rect.top - 6, building.rect.width, 4)
                bar_fg = pygame.Rect(bar_bg.left, bar_bg.top, int(bar_bg.width * hp_ratio), bar_bg.height)
                pygame.draw.rect(surface, (70, 18, 18), bar_bg)
                pygame.draw.rect(surface, (40, 210, 60), bar_fg)
        # Border
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 4)
