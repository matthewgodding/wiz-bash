import pygame
import math

# type: "projectile" fires a Projectile toward the opponent
#       "instant"    resolves immediately on the caster (defensive)
SPELL_DEFS = [
    # --- offensive ---
    {"name": "Fireball",       "type": "projectile", "mana": 25, "damage": 30, "speed": 6,  "color": (255, 100,  20), "radius": 10, "effect": None,        "cooldown": 600},
    {"name": "Frost Bolt",     "type": "projectile", "mana": 20, "damage": 15, "speed": 5,  "color": ( 80, 200, 255), "radius":  8, "effect": "slow",      "cooldown": 700},
    {"name": "Lightning",      "type": "projectile", "mana": 30, "damage": 40, "speed": 18, "color": (255, 255,  80), "radius":  5, "effect": None,        "cooldown": 900},
    {"name": "Arcane Missile", "type": "projectile", "mana": 10, "damage": 12, "speed": 7,  "color": (200,  80, 255), "radius":  6, "effect": None,        "cooldown": 350},
    {"name": "Mana Drain",     "type": "projectile", "mana": 15, "damage":  5, "speed": 5,  "color": ( 80, 255, 180), "radius":  7, "effect": "manadrain", "cooldown": 800},
    # --- defensive ---
    {"name": "Shield",         "type": "instant",    "mana": 20, "damage":  0, "speed": 0,  "color": (180, 220, 255), "radius":  0, "effect": "shield",    "cooldown": 3000},
    {"name": "Blink",          "type": "instant",    "mana": 25, "damage":  0, "speed": 0,  "color": (160,  80, 255), "radius":  0, "effect": "blink",     "cooldown": 2500},
    {"name": "Counterspell",   "type": "instant",    "mana": 30, "damage":  0, "speed": 0,  "color": (255, 200,  60), "radius":  0, "effect": "counter",   "cooldown": 2000},
    {"name": "Heal",           "type": "instant",    "mana": 35, "damage":  0, "speed": 0,  "color": ( 80, 255, 120), "radius":  0, "effect": "heal",      "cooldown": 4000},
]

COUNTER_RADIUS = 120   # pixels — destroys projectiles within this range
HEAL_AMOUNT    = 30
SHIELD_HITS    = 1     # absorbs this many projectile hits


class Projectile:
    def __init__(self, x, y, dx, dy, owner, spell_def):
        self.x = float(x)
        self.y = float(y)
        self.dx = dx
        self.dy = dy
        self.owner = owner
        self.spell = spell_def
        self.alive = True
        self.trail = []

    def update(self, dt, arena_rect):
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.x += self.dx
        self.y += self.dy
        if not arena_rect.collidepoint(self.x, self.y):
            self.alive = False

    def check_hit(self, target):
        if not target.is_alive():
            return False
        dist = math.hypot(self.x - (target.x + target.size // 2),
                          self.y - (target.y + target.size // 2))
        return dist < self.spell["radius"] + target.size // 2

    def apply(self, target):
        # Shield absorbs the hit
        if target.shield > 0:
            target.shield -= 1
            target.shield_flash = 300  # ms visual flash
            self.alive = False
            return
        target.take_damage(self.spell["damage"])
        effect = self.spell["effect"]
        if effect == "slow":
            target.slow_timer = 3000
        elif effect == "manadrain":
            stolen = min(20, target.mana)
            target.mana -= stolen
            self.owner.mana = min(self.owner.max_mana, self.owner.mana + stolen)
        self.alive = False

    def draw(self, surface):
        color = self.spell["color"]
        r = self.spell["radius"]

        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(180 * (i / max(len(self.trail), 1)))
            tr = max(1, r - (len(self.trail) - i))
            trail_surf = pygame.Surface((tr * 2 + 2, tr * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*color, alpha), (tr + 1, tr + 1), tr)
            surface.blit(trail_surf, (tx - tr - 1, ty - tr - 1))

        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 80), (r * 2, r * 2), r * 2)
        surface.blit(glow, (int(self.x) - r * 2, int(self.y) - r * 2))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x) - r // 3, int(self.y) - r // 3), max(1, r // 3))
