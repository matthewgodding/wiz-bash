import pygame
import math

# type: "projectile" fires a Projectile toward the opponent
#       "instant"    resolves immediately on the caster (defensive)
#       "summon"     creates a temporary ally or one-shot summon effect
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
    # --- mythical summons ---
    {"name": "Phoenix Dive",   "type": "summon",     "mana": 35, "damage": 24, "speed": 0,  "color": (255, 130,  40), "radius": 10, "effect": "summon",    "cooldown": 2600, "summon_type": "one_shot", "creature": "phoenix"},
    {"name": "Minotaur",       "type": "summon",     "mana": 30, "damage": 12, "speed": 2.6,"color": (180, 120,  80), "radius": 18, "effect": "summon",    "cooldown": 2400, "summon_type": "ally", "creature": "minotaur", "lifetime": 7000, "hp": 48, "attack_cooldown": 750},
    {"name": "Griffin",        "type": "summon",     "mana": 28, "damage": 10, "speed": 3.2,"color": (230, 220, 120), "radius": 14, "effect": "summon",    "cooldown": 2200, "summon_type": "ally", "creature": "griffin", "lifetime": 6000, "hp": 34, "attack_cooldown": 600},
    {"name": "Dragon Whelp",   "type": "summon",     "mana": 34, "damage":  9, "speed": 2.2,"color": (210,  80, 255), "radius": 15, "effect": "summon",    "cooldown": 2800, "summon_type": "ally", "creature": "whelp", "lifetime": 7000, "hp": 30, "attack_cooldown": 500, "attack_range": 170},
    {"name": "Golem Guard",    "type": "summon",     "mana": 32, "damage":  8, "speed": 1.8,"color": (140, 150, 170), "radius": 20, "effect": "summon",    "cooldown": 3000, "summon_type": "ally", "creature": "golem", "lifetime": 8000, "hp": 70, "attack_cooldown": 850},
]

COUNTER_RADIUS = 120   # pixels — destroys projectiles within this range
HEAL_AMOUNT    = 30
SHIELD_HITS    = 1     # absorbs this many projectile hits


class SummonedCreature:
    def __init__(self, owner, spell_def, x, y):
        self.owner = owner
        self.spell = spell_def
        self.creature = spell_def.get("creature", "beast")
        self.x = float(x)
        self.y = float(y)
        self.size = int(spell_def.get("radius", 16)) * 2
        self.hp = float(spell_def.get("hp", 30))
        self.max_hp = float(spell_def.get("hp", 30))
        self.mana = 0.0
        self.max_mana = 0.0
        self.shield = 0
        self.slow_timer = 0
        self.alive = True
        self.lifetime_ms = int(spell_def.get("lifetime", 6000))
        self.age_ms = 0
        self.attack_cooldown = int(spell_def.get("attack_cooldown", 650))
        self.attack_timer = 0
        self.attack_range = float(spell_def.get("attack_range", 60))

    @property
    def center(self):
        return (self.x + self.size / 2, self.y + self.size / 2)

    def take_damage(self, amount):
        self.hp = max(0.0, self.hp - amount)
        if self.hp <= 0:
            self.alive = False

    def is_alive(self):
        return self.alive

    def collides_with_projectile(self, projectile):
        cx, cy = self.center
        dist = math.hypot(projectile.x - cx, projectile.y - cy)
        return dist < projectile.spell["radius"] + self.size / 2

    def _choose_target(self, enemy_player, enemy_summons):
        if enemy_player.is_alive():
            return enemy_player
        for summon in enemy_summons:
            if summon.alive:
                return summon
        return None

    def update(self, dt, arena_rect, enemy_player, enemy_summons, projectiles):
        if not self.alive:
            return
        self.age_ms += dt
        if self.age_ms >= self.lifetime_ms or not self.owner.is_alive():
            self.alive = False
            return
        if self.slow_timer > 0:
            self.slow_timer = max(0, self.slow_timer - dt)

        target = self._choose_target(enemy_player, enemy_summons)
        if target is None:
            return

        tx, ty = target.center
        sx, sy = self.center
        dist = math.hypot(tx - sx, ty - sy) or 1.0
        move_speed = self.spell.get("speed", 2.2)
        if self.slow_timer > 0:
            move_speed *= 0.65

        if self.creature == "golem":
            # Stay near owner and intercept projectiles around them.
            ox, oy = self.owner.center
            odist = math.hypot(ox - sx, oy - sy) or 1.0
            if odist > 85:
                self.x += (ox - sx) / odist * move_speed
                self.y += (oy - sy) / odist * move_speed
            for proj in projectiles:
                if proj.owner is self.owner:
                    continue
                if math.hypot(proj.x - sx, proj.y - sy) <= 35:
                    proj.alive = False
        elif dist > self.attack_range:
            self.x += (tx - sx) / dist * move_speed
            self.y += (ty - sy) / dist * move_speed

        self.x = max(arena_rect.left, min(arena_rect.right - self.size, self.x))
        self.y = max(arena_rect.top, min(arena_rect.bottom - self.size, self.y))

        self.attack_timer = max(0, self.attack_timer - dt)
        if self.attack_timer > 0:
            return

        if dist <= self.attack_range:
            if self.creature == "whelp":
                cx, cy = self.center
                vdx = (tx - cx) / dist * 5
                vdy = (ty - cy) / dist * 5
                breath = {
                    "name": "Whelp Ember",
                    "damage": self.spell["damage"],
                    "speed": 5,
                    "color": self.spell["color"],
                    "radius": 5,
                    "effect": None,
                    "cooldown": 0,
                }
                projectiles.append(Projectile(cx, cy, vdx, vdy, self.owner, breath))
            else:
                target.take_damage(self.spell["damage"])
            self.attack_timer = self.attack_cooldown

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        w = self.size
        base = self.spell["color"]
        team_tint = tuple(min(255, int((bc + oc) * 0.55)) for bc, oc in zip(base, self.owner.color))
        cx, cy = x + w // 2, y + w // 2

        if self.creature == "minotaur":
            body = pygame.Rect(x + w // 5, y + w // 3, w * 3 // 5, w // 2)
            pygame.draw.ellipse(surface, team_tint, body)
            pygame.draw.circle(surface, team_tint, (cx, y + w // 4), w // 5)
            horn_col = (230, 220, 180)
            pygame.draw.polygon(surface, horn_col, [(cx - w // 6, y + w // 6), (cx - w // 3, y + w // 10), (cx - w // 5, y + w // 4)])
            pygame.draw.polygon(surface, horn_col, [(cx + w // 6, y + w // 6), (cx + w // 3, y + w // 10), (cx + w // 5, y + w // 4)])
        elif self.creature == "griffin":
            body = pygame.Rect(x + w // 4, y + w // 3, w // 2, w // 2)
            pygame.draw.ellipse(surface, team_tint, body)
            wing_col = tuple(min(255, c + 35) for c in team_tint)
            pygame.draw.polygon(surface, wing_col, [(cx - w // 8, cy), (x + w // 12, y + w // 4), (cx - w // 10, y + w // 2)])
            pygame.draw.polygon(surface, wing_col, [(cx + w // 8, cy), (x + w - w // 12, y + w // 4), (cx + w // 10, y + w // 2)])
            pygame.draw.circle(surface, (240, 225, 170), (cx + w // 6, y + w // 3), w // 7)
            beak = [(cx + w // 4, y + w // 3), (cx + w // 3, y + w // 3 + 2), (cx + w // 4, y + w // 3 + 6)]
            pygame.draw.polygon(surface, (240, 180, 70), beak)
        elif self.creature == "whelp":
            body = pygame.Rect(x + w // 5, y + w // 3, w * 3 // 5, w // 2)
            pygame.draw.ellipse(surface, team_tint, body)
            pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in team_tint), [(cx - w // 6, y + w // 3), (cx, y + w // 8), (cx + w // 6, y + w // 3)])
            pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in team_tint), [(cx - w // 10, y + w // 2), (cx, y + w // 3), (cx + w // 10, y + w // 2)])
            pygame.draw.circle(surface, (255, 200, 120), (cx + w // 6, y + w // 2), w // 10)
        elif self.creature == "golem":
            body = pygame.Rect(x + w // 5, y + w // 4, w * 3 // 5, w * 3 // 5)
            pygame.draw.rect(surface, team_tint, body, border_radius=3)
            crack_col = (70, 70, 80)
            pygame.draw.line(surface, crack_col, (x + w // 3, y + w // 3), (x + w // 2, y + w // 2), 2)
            pygame.draw.line(surface, crack_col, (x + w // 2, y + w // 2), (x + w * 2 // 3, y + w // 3), 2)
            arm_col = tuple(max(0, c - 15) for c in team_tint)
            pygame.draw.rect(surface, arm_col, (x + w // 10, y + w // 3, w // 7, w // 3), border_radius=2)
            pygame.draw.rect(surface, arm_col, (x + w - w // 10 - w // 7, y + w // 3, w // 7, w // 3), border_radius=2)
        else:
            pygame.draw.circle(surface, team_tint, (cx, cy), w // 2)

        pygame.draw.circle(surface, (20, 20, 25), (cx, cy), w // 2, 2)
        pygame.draw.circle(surface, (255, 255, 255), (cx - w // 7, cy - w // 7), max(2, w // 12))
        hp_ratio = 0 if self.max_hp <= 0 else self.hp / self.max_hp
        pygame.draw.rect(surface, (70, 0, 0), (x, y - 6, w, 4))
        pygame.draw.rect(surface, (0, 190, 0), (x, y - 6, int(w * hp_ratio), 4))


class OneShotSummon:
    def __init__(self, owner, target, spell_def):
        self.owner = owner
        self.target = target
        self.spell = spell_def
        self.alive = True
        self.age_ms = 0
        self.duration_ms = 220
        self.resolved = False
        ox, oy = owner.center
        tx, ty = target.center
        self.x = ox
        self.y = oy
        self.tx = tx
        self.ty = ty

    def update(self, dt, _arena_rect, _enemy_player, _enemy_summons, _projectiles):
        if not self.alive:
            return
        self.age_ms += dt
        if not self.resolved:
            self.target.take_damage(self.spell["damage"])
            self.resolved = True
        if self.age_ms >= self.duration_ms:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        progress = min(1.0, self.age_ms / self.duration_ms)
        cx = int(self.x + (self.tx - self.x) * progress)
        cy = int(self.y + (self.ty - self.y) * progress)
        color = self.spell["color"]
        # Stylized phoenix head + wings for one-shot dive silhouette.
        wing_col = tuple(min(255, c + 40) for c in color)
        pygame.draw.polygon(surface, wing_col, [(cx - 14, cy + 4), (cx - 4, cy - 8), (cx - 2, cy + 6)])
        pygame.draw.polygon(surface, wing_col, [(cx + 14, cy + 4), (cx + 4, cy - 8), (cx + 2, cy + 6)])
        pygame.draw.ellipse(surface, color, (cx - 7, cy - 6, 14, 12))
        beak = [(cx + 6, cy - 2), (cx + 11, cy), (cx + 6, cy + 2)]
        pygame.draw.polygon(surface, (250, 220, 120), beak)
        flame = tuple(min(255, c + 55) for c in color)
        pygame.draw.circle(surface, flame, (cx, cy + 9), 4)


def create_summon_effect(owner, target, spell_def, arena_rect):
    if spell_def.get("summon_type") == "one_shot":
        return OneShotSummon(owner, target, spell_def)
    sx = owner.x + owner.size // 2 - spell_def["radius"]
    sy = owner.y + owner.size // 2 - spell_def["radius"]
    summon = SummonedCreature(owner, spell_def, sx, sy)
    summon.x = max(arena_rect.left, min(arena_rect.right - summon.size, summon.x))
    summon.y = max(arena_rect.top, min(arena_rect.bottom - summon.size, summon.y))
    return summon


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
