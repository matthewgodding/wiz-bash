import pygame
import math
import random
from spells import SPELL_DEFS, Projectile, COUNTER_RADIUS, HEAL_AMOUNT, SHIELD_HITS, create_summon_effect
from arena import resolve_actor_move

PLAYER_SPEED = 4
MANA_REGEN = 3  # mana per second


class Player:
    def __init__(self, name, x, y, color, controls):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.controls = controls
        self.hp = 100
        self.max_hp = 100
        self.mana = 100
        self.max_mana = 100
        self.size = 40
        self.selected_spell = 0
        self.spell_cooldowns = [0] * len(SPELL_DEFS)
        # status effects
        self.slow_timer = 0
        self.shield = 0          # charges remaining
        self.shield_flash = 0    # ms of visual flash after absorbing a hit
        self.counter_flash = 0   # ms of counterspell ring visual
        self.blink_flash = 0     # ms of blink afterimage visual
        self.heal_flash = 0      # ms of heal glow visual
        self.casting = False
        self.cast_timer = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    @property
    def center(self):
        return (int(self.x) + self.size // 2, int(self.y) + self.size // 2)

    @property
    def current_spell(self):
        return SPELL_DEFS[self.selected_spell]

    def handle_input(self, keys, arena_rect, actions=None, obstacles=None):
        speed = PLAYER_SPEED // 2 if self.slow_timer > 0 else PLAYER_SPEED
        dx, dy = 0, 0
        if keys[self.controls["up"]]:    dy -= speed
        if keys[self.controls["down"]]:  dy += speed
        if keys[self.controls["left"]]:  dx -= speed
        if keys[self.controls["right"]]: dx += speed
        if actions is not None:
            if actions.get("up"):    dy -= speed
            if actions.get("down"):  dy += speed
            if actions.get("left"):  dx -= speed
            if actions.get("right"): dx += speed
        if obstacles:
            moved = resolve_actor_move(self.rect, dx, dy, arena_rect, obstacles)
            self.x = float(moved.x)
            self.y = float(moved.y)
        else:
            self.x = max(arena_rect.left, min(arena_rect.right - self.size, self.x + dx))
            self.y = max(arena_rect.top,  min(arena_rect.bottom - self.size, self.y + dy))

    def handle_spell_switch(self, event):
        if event.key == self.controls["spell_next"]:
            self.selected_spell = (self.selected_spell + 1) % len(SPELL_DEFS)
        elif event.key == self.controls["spell_prev"]:
            self.selected_spell = (self.selected_spell - 1) % len(SPELL_DEFS)

    def handle_spell_switch_action(self, actions):
        if actions.get("spell_next"):
            self.selected_spell = (self.selected_spell + 1) % len(SPELL_DEFS)
        elif actions.get("spell_prev"):
            self.selected_spell = (self.selected_spell - 1) % len(SPELL_DEFS)

    def try_cast(self, keys, now, target, projectiles, arena_rect, actions=None, sound_manager=None, arena=None):
        """Returns a new Projectile or None. Instant spells resolve here."""
        cast_pressed = bool(keys[self.controls["cast"]])
        if actions is not None:
            cast_pressed = cast_pressed or bool(actions.get("cast"))
        if not cast_pressed:
            return None
        spell = self.current_spell
        if now - self.spell_cooldowns[self.selected_spell] < spell["cooldown"]:
            return None
        if self.mana < spell["mana"]:
            return None

        self.mana -= spell["mana"]
        self.spell_cooldowns[self.selected_spell] = now
        self.casting = True
        self.cast_timer = 200
        if sound_manager is not None:
            sound_manager.play_spell(spell["name"])

        if spell["type"] == "instant":
            self._apply_instant(spell, target, projectiles, arena_rect, arena=arena)
            return None
        if spell["type"] == "summon":
            return create_summon_effect(self, target, spell, arena_rect)

        # Projectile — aim at opponent
        cx, cy = self.center
        tx, ty = target.center
        dist = math.hypot(tx - cx, ty - cy) or 1
        dx = (tx - cx) / dist * spell["speed"]
        dy = (ty - cy) / dist * spell["speed"]
        return Projectile(cx, cy, dx, dy, self, spell, target=target)

    def _apply_instant(self, spell, target, projectiles, arena_rect, arena=None):
        effect = spell["effect"]

        if effect == "shield":
            self.shield = SHIELD_HITS
            self.shield_flash = 600

        elif effect == "blink":
            # Teleport to a random spot on the far side of the arena from the opponent
            cx, cy = self.center
            tx, ty = target.center
            # Pick a point roughly opposite the opponent
            ax = arena_rect.left + random.randint(20, arena_rect.width - self.size - 20)
            ay = arena_rect.top  + random.randint(20, arena_rect.height - self.size - 20)
            # Bias away from opponent: try a few candidates, pick the farthest
            best, best_dist = (ax, ay), 0
            for _ in range(8):
                cx2 = arena_rect.left + random.randint(20, arena_rect.width - self.size - 20)
                cy2 = arena_rect.top  + random.randint(20, arena_rect.height - self.size - 20)
                d = math.hypot(cx2 - tx, cy2 - ty)
                if d > best_dist:
                    best, best_dist = (cx2, cy2), d
            if arena is not None:
                # Try several candidates and pick the best valid one.
                valid = []
                for _ in range(12):
                    vx = arena_rect.left + random.randint(20, arena_rect.width - self.size - 20)
                    vy = arena_rect.top + random.randint(20, arena_rect.height - self.size - 20)
                    candidate_rect = pygame.Rect(vx, vy, self.size, self.size)
                    if arena.is_spawn_valid(candidate_rect):
                        valid.append((vx, vy))
                if valid:
                    self.x, self.y = float(valid[0][0]), float(valid[0][1])
                else:
                    self.x, self.y = float(best[0]), float(best[1])
            else:
                self.x, self.y = float(best[0]), float(best[1])
            self.blink_flash = 400

        elif effect == "counter":
            # Destroy all enemy projectiles within COUNTER_RADIUS
            cx, cy = self.center
            for p in projectiles:
                if p.owner is not self:
                    dist = math.hypot(p.x - cx, p.y - cy)
                    if dist < COUNTER_RADIUS:
                        p.alive = False
            self.counter_flash = 500

        elif effect == "heal":
            self.hp = min(self.max_hp, self.hp + HEAL_AMOUNT)
            self.heal_flash = 600

    def update(self, dt):
        if self.slow_timer   > 0: self.slow_timer   = max(0, self.slow_timer   - dt)
        if self.shield_flash > 0: self.shield_flash = max(0, self.shield_flash - dt)
        if self.counter_flash> 0: self.counter_flash= max(0, self.counter_flash- dt)
        if self.blink_flash  > 0: self.blink_flash  = max(0, self.blink_flash  - dt)
        if self.heal_flash   > 0: self.heal_flash   = max(0, self.heal_flash   - dt)
        if self.casting:
            self.cast_timer -= dt
            if self.cast_timer <= 0:
                self.casting = False
        self.mana = min(self.max_mana, self.mana + MANA_REGEN * dt / 1000)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def is_alive(self):
        return self.hp > 0

    # ------------------------------------------------------------------ drawing

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        w, h = self.size, self.size
        cx = x + w // 2

        robe      = self.color if self.is_alive() else (80, 80, 80)
        dark      = tuple(max(0, c - 60) for c in robe)
        skin      = (255, 220, 170) if self.is_alive() else (130, 130, 130)
        star_col  = (255, 240, 80)
        staff_col = (160, 110, 50)

        # --- defensive effect visuals ---
        # Counterspell ring
        if self.counter_flash > 0:
            ratio = self.counter_flash / 500
            ring_r = int(COUNTER_RADIUS * (1 - ratio * 0.3))
            ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (255, 200, 60, int(180 * ratio)), (ring_r + 2, ring_r + 2), ring_r, 3)
            surface.blit(ring_surf, (cx - ring_r - 2, y + h // 2 - ring_r - 2))

        # Heal glow
        if self.heal_flash > 0:
            ratio = self.heal_flash / 600
            glow = pygame.Surface((w + 30, h + 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 255, 120, int(120 * ratio)), (w // 2 + 15, h // 2 + 15), 28)
            surface.blit(glow, (x - 15, y - 15))

        # Blink afterimage
        if self.blink_flash > 0:
            ratio = self.blink_flash / 400
            ghost = pygame.Surface((w, h), pygame.SRCALPHA)
            ghost.fill((*robe, int(80 * ratio)))
            surface.blit(ghost, (x, y))

        # Slow tint
        if self.slow_timer > 0:
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill((80, 200, 255, 60))
            surface.blit(tint, (x, y))

        # Shield bubble
        if self.shield > 0 or self.shield_flash > 0:
            alpha = 180 if self.shield > 0 else int(180 * self.shield_flash / 600)
            shield_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (180, 220, 255, alpha), (w // 2 + 10, h // 2 + 10), w // 2 + 8, 3)
            surface.blit(shield_surf, (x - 10, y - 10))

        # robe
        robe_top_y = y + 20
        pygame.draw.polygon(surface, robe, [
            (cx - 7,  robe_top_y), (cx + 7,  robe_top_y),
            (cx + 11, y + h),      (cx - 11, y + h),
        ])
        pygame.draw.polygon(surface, dark, [
            (cx - 2, robe_top_y), (cx + 2, robe_top_y),
            (cx + 3, y + h),      (cx - 3, y + h),
        ])

        # head
        head_cy = y + 18
        pygame.draw.circle(surface, skin, (cx, head_cy), 7)
        pygame.draw.circle(surface, (40, 20, 80), (cx - 3, head_cy - 1), 2)
        pygame.draw.circle(surface, (40, 20, 80), (cx + 3, head_cy - 1), 2)
        pygame.draw.ellipse(surface, (220, 220, 220), (cx - 4, head_cy + 3, 8, 6))

        # hat
        pygame.draw.polygon(surface, dark, [(cx, y), (cx - 9, y + 14), (cx + 9, y + 14)])
        pygame.draw.ellipse(surface, dark, (cx - 11, y + 12, 22, 6))
        self._draw_star(surface, star_col, (cx, y + 6), 4)

        # staff
        staff_x = cx - 15
        pygame.draw.line(surface, staff_col, (staff_x, y + 10), (staff_x, y + h), 3)
        orb_color = self.current_spell["color"] if self.is_alive() else (80, 80, 80)
        pygame.draw.circle(surface, orb_color, (staff_x, y + 9), 5)
        pygame.draw.circle(surface, (255, 255, 255), (staff_x - 1, y + 7), 2)

        # cast burst
        if self.casting:
            burst = pygame.Surface((w + 40, h + 40), pygame.SRCALPHA)
            sc = self.current_spell["color"]
            pygame.draw.circle(burst, (*sc, 80), (w // 2 + 20, h // 2 + 20), 30)
            pygame.draw.circle(burst, (255, 255, 255, 60), (w // 2 + 20, h // 2 + 20), 15)
            surface.blit(burst, (x - 20, y - 20))

        # HP / mana bars
        self._draw_bar(surface, x, y - 12, self.size, 6, self.hp / self.max_hp, (0, 200, 0), (60, 0, 0))
        self._draw_bar(surface, x, y - 5,  self.size, 4, self.mana / self.max_mana, (60, 80, 255), (0, 0, 60))

        # name
        font = pygame.font.SysFont(None, 20)
        surface.blit(font.render(self.name, True, (255, 255, 255)), (x, y - 26))

    def _draw_bar(self, surface, bx, by, bw, bh, ratio, fg, bg):
        pygame.draw.rect(surface, bg, (bx, by, bw, bh))
        pygame.draw.rect(surface, fg, (bx, by, int(bw * max(0, ratio)), bh))

    def _draw_star(self, surface, color, center, radius):
        cx, cy = center
        points = []
        for i in range(8):
            angle = math.pi / 4 * i - math.pi / 2
            r = radius if i % 2 == 0 else radius // 2
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)
