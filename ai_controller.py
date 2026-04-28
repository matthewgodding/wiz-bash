from __future__ import annotations

import math
import random
from dataclasses import dataclass
from player import Player, PLAYER_SPEED
from spells import SPELL_DEFS, Projectile, create_summon_effect


@dataclass
class DifficultyConfig:
    name: str
    reaction_delay: int    # ms — how often AI re-evaluates decisions
    cast_accuracy: float   # 0.0–1.0 — probability AI actually fires when it "wants" to
    ignore_threat_prob: float  # probability AI ignores a detected threat (Easy: 0.4, others: 0.0)
    random_spell_select: bool  # True on Easy — pick offensive spell randomly


EASY   = DifficultyConfig("Easy",   reaction_delay=800, cast_accuracy=0.60, ignore_threat_prob=0.40, random_spell_select=True)
MEDIUM = DifficultyConfig("Medium", reaction_delay=400, cast_accuracy=0.85, ignore_threat_prob=0.00, random_spell_select=False)
HARD   = DifficultyConfig("Hard",   reaction_delay=100, cast_accuracy=1.00, ignore_threat_prob=0.00, random_spell_select=False)


def _lead_target(ai_wizard: Player, human: Player, spell_speed: float,
                 human_vel: tuple[float, float]) -> tuple[float, float]:
    """
    Returns the predicted position of the human at the time a projectile
    fired now would reach them, assuming constant velocity.
    Falls back to current human centre if no solution exists.
    """
    hx, hy = human.center
    if spell_speed <= 0:
        return hx, hy
    vx, vy = human_vel
    if vx == 0 and vy == 0:
        return hx, hy
    ax, ay = ai_wizard.center
    dist = math.hypot(hx - ax, hy - ay)
    t = dist / spell_speed
    return hx + vx * t, hy + vy * t


def _is_threat(proj: Projectile, ai_wizard: Player) -> bool:
    """Return True if the projectile is on a collision course with the AI wizard."""
    ax, ay = ai_wizard.center
    rx, ry = ax - proj.x, ay - proj.y
    speed_sq = proj.dx**2 + proj.dy**2
    if speed_sq == 0:
        return False
    t = (rx * proj.dx + ry * proj.dy) / speed_sq
    if t < 0:
        return False  # already passed
    cx = proj.x + proj.dx * t
    cy = proj.y + proj.dy * t
    dist = math.hypot(cx - ax, cy - ay)
    return dist < ai_wizard.size * 1.5


class AIController:
    def __init__(self, ai_wizard: Player, config: DifficultyConfig, sound_manager=None) -> None:
        self.ai_wizard = ai_wizard
        self.config = config
        self.sound_manager = sound_manager

        # Timestamp gates — initialised to 0 so the AI can act immediately
        self._next_move_time: int = 0
        self._next_cast_time: int = 0
        self._next_summon_time: int = 0

        # Current movement direction (unit-ish vector components)
        self._move_dx: float = 0.0
        self._move_dy: float = 0.0

        # Human position tracking for velocity estimation
        self._prev_human_pos: tuple = (0, 0)
        self._prev_human_time: int = 0

    def _choose_movement(self, human: Player, threats: list, arena_rect, now: int) -> tuple[float, float]:
        """Return a (dx, dy) unit vector for the AI wizard's movement this frame."""
        # Gate: only update direction once per reaction_delay
        if now < self._next_move_time:
            return (self._move_dx, self._move_dy)

        self._next_move_time = now + self.config.reaction_delay

        ax, ay = self.ai_wizard.center
        dx, dy = 0.0, 0.0

        if threats:
            # Evade: move perpendicular to the first threat's velocity
            threat = threats[0]
            tdx, tdy = threat.dx, threat.dy
            speed = math.hypot(tdx, tdy)
            if speed > 0:
                # Two perpendicular options; pick the one that moves away from the threat
                perp1 = (-tdy / speed,  tdx / speed)
                perp2 = ( tdy / speed, -tdx / speed)
                # Choose the option that moves the AI further from the threat origin
                tx, ty = threat.x, threat.y
                d1 = (ax + perp1[0] - tx) ** 2 + (ay + perp1[1] - ty) ** 2
                d2 = (ax + perp2[0] - tx) ** 2 + (ay + perp2[1] - ty) ** 2
                dx, dy = perp1 if d1 >= d2 else perp2
            else:
                dx, dy = 0.0, 0.0
        else:
            # No threat: maintain 200–350 px engagement band
            hx, hy = human.center
            dist = math.hypot(hx - ax, hy - ay)
            if dist > 0:
                # Unit vector toward human
                toward_x = (hx - ax) / dist
                toward_y = (hy - ay) / dist
                if dist > 350:
                    # Too far — move toward human
                    dx, dy = toward_x, toward_y
                elif dist < 200:
                    # Too close — move away from human
                    dx, dy = -toward_x, -toward_y
                # else: already in band — no radial movement needed (dx, dy stay 0)

        # Boundary avoidance: add inward component when within 80 px of any edge
        BOUNDARY_MARGIN = 80
        bx, by = 0.0, 0.0
        if ax - arena_rect.left < BOUNDARY_MARGIN:
            bx += 1.0
        if arena_rect.right - ax < BOUNDARY_MARGIN:
            bx -= 1.0
        if ay - arena_rect.top < BOUNDARY_MARGIN:
            by += 1.0
        if arena_rect.bottom - ay < BOUNDARY_MARGIN:
            by -= 1.0

        dx += bx
        dy += by

        # Normalize to unit vector
        mag = math.hypot(dx, dy)
        if mag > 0:
            dx /= mag
            dy /= mag

        self._move_dx = dx
        self._move_dy = dy
        return (self._move_dx, self._move_dy)

    def _choose_spell(self, human: Player, now: int) -> int | None:
        """Return an offensive spell index to cast, or None."""
        # Requirement 4.5: suppress offensive casting when mana < 20
        if self.ai_wizard.mana < 20:
            return None

        # Respect cast_accuracy — skip with probability (1 - cast_accuracy)
        if random.random() > self.config.cast_accuracy:
            return None

        # Estimate human velocity from previous position
        dt = now - self._prev_human_time
        if dt > 0:
            hx, hy = human.center
            px, py = self._prev_human_pos
            human_vel: tuple[float, float] = ((hx - px) / dt, (hy - py) / dt)
        else:
            human_vel = (0.0, 0.0)

        # Update tracking state
        self._prev_human_pos = human.center
        self._prev_human_time = now

        # Offensive spells are indices 0–4
        OFFENSIVE_RANGE = range(5)

        def is_available(i: int) -> bool:
            spell = SPELL_DEFS[i]
            off_cooldown = (now - self.ai_wizard.spell_cooldowns[i]) >= spell["cooldown"]
            affordable = self.ai_wizard.mana >= spell["mana"]
            return off_cooldown and affordable

        available = [i for i in OFFENSIVE_RANGE if is_available(i)]
        if not available:
            return None

        # Easy: uniform random selection (Requirement 6.4)
        if self.config.random_spell_select:
            return random.choice(available)

        # Medium/Hard: preference logic (Requirement 4.2)
        hx, hy = human.center
        human_speed = math.hypot(human_vel[0], human_vel[1])

        if human_speed > 3:
            # Prefer fastest-projectile spell
            preferred = max(available, key=lambda i: SPELL_DEFS[i]["speed"])
        else:
            # Prefer highest-damage spell when human HP > 50%
            hp_ratio = human.hp / human.max_hp
            if hp_ratio > 0.5:
                preferred = max(available, key=lambda i: SPELL_DEFS[i]["damage"])
            else:
                # Fall back to first available
                preferred = available[0]

        return preferred

    def _should_cast_defensive(self, human: Player, threats: list, now: int) -> int | None:
        """Return a defensive spell index to cast, or None.

        Priority order:
          1. Counterspell (index 7) — multiple threats (>= 2)
          2. Shield (index 5)       — single threat, HP-proportional probability
          3. Blink (index 6)        — threat present, Shield/Counterspell unavailable
          4. Heal (index 8)         — HP < 30%, no threat

        Mana suppression (Req 5.5):
          - If mana < 30 and hp >= 15% of max_hp → return None
          - If mana < 30 and hp < 15% of max_hp  → only Heal allowed (if available)
        """
        ai = self.ai_wizard
        hp_ratio = ai.hp / ai.max_hp

        def is_available(i: int) -> bool:
            spell = SPELL_DEFS[i]
            off_cooldown = (now - ai.spell_cooldowns[i]) >= spell["cooldown"]
            affordable = ai.mana >= spell["mana"]
            return off_cooldown and affordable

        # Mana suppression
        if ai.mana < 30:
            if hp_ratio >= 0.15:
                return None
            # HP < 15%: only Heal is allowed
            if is_available(8):
                return 8
            return None

        # Normal priority logic
        if len(threats) >= 2:
            # Priority 1: Counterspell
            if is_available(7):
                return 7

        if threats:
            # Priority 2: Shield (HP-proportional probability)
            if is_available(5):
                if random.random() < (1 - hp_ratio):
                    return 5

            # Priority 3: Blink (threat present, Shield/Counterspell unavailable)
            if is_available(6):
                return 6

        # Priority 4: Heal (HP < 30%, no threat)
        if not threats and hp_ratio < 0.30:
            if is_available(8):
                return 8

        return None

    def _choose_summon_spell(self, now: int) -> int | None:
        if now < self._next_summon_time:
            return None
        summon_indices = [i for i, spell in enumerate(SPELL_DEFS) if spell.get("type") == "summon"]
        available = [
            i for i in summon_indices
            if self.ai_wizard.mana >= SPELL_DEFS[i]["mana"]
            and (now - self.ai_wizard.spell_cooldowns[i]) >= SPELL_DEFS[i]["cooldown"]
        ]
        if not available:
            return None
        # Keep summon cadence moderate so AI still uses baseline offensive spells.
        self._next_summon_time = now + 2200
        # Prefer temporary ally summons over one-shot when both are available.
        allies = [i for i in available if SPELL_DEFS[i].get("summon_type") == "ally"]
        if allies:
            return random.choice(allies)
        return random.choice(available)

    def update(self, now: int, dt: int, human: Player, projectiles: list, arena_rect) -> object:
        """Called once per frame. Returns a new Projectile if the AI casts, otherwise None."""
        ai = self.ai_wizard

        # Step 1: Detect threats — projectiles owned by the human heading toward the AI
        threats = [p for p in projectiles if p.owner is human and _is_threat(p, ai)]

        # Step 2 (Task 6.1): Easy stochastic threat-ignore — filter threats before passing
        # to movement and defensive logic
        if self.config.ignore_threat_prob > 0:
            effective_threats = [t for t in threats if random.random() >= self.config.ignore_threat_prob]
        else:
            effective_threats = threats

        # Step 3: Choose movement direction
        dx, dy = self._choose_movement(human, effective_threats, arena_rect, now)

        # Step 4: Apply movement clamped to arena bounds
        new_x = ai.x + dx * PLAYER_SPEED
        new_y = ai.y + dy * PLAYER_SPEED
        ai.x = max(arena_rect.left, min(arena_rect.right - ai.size, new_x))
        ai.y = max(arena_rect.top,  min(arena_rect.bottom - ai.size, new_y))

        # Step 5: Defensive spell
        def_idx = self._should_cast_defensive(human, effective_threats, now)
        if def_idx is not None:
            spell = SPELL_DEFS[def_idx]
            # Safety check: mana and cooldown (already verified in _should_cast_defensive, but be safe)
            if (ai.mana >= spell["mana"] and
                    (now - ai.spell_cooldowns[def_idx]) >= spell["cooldown"]):
                ai.mana -= spell["mana"]
                ai.spell_cooldowns[def_idx] = now
                ai._apply_instant(spell, human, projectiles, arena_rect)
                if self.sound_manager is not None:
                    self.sound_manager.play_spell(spell["name"])

        # Step 6: Estimate human velocity before calling _choose_spell
        # (velocity is also computed inside _choose_spell, but we need it here for lead aim)
        vel_dt = now - self._prev_human_time
        if vel_dt > 0:
            hx, hy = human.center
            px, py = self._prev_human_pos
            human_vel: tuple[float, float] = ((hx - px) / vel_dt, (hy - py) / vel_dt)
        else:
            human_vel = (0.0, 0.0)

        # _choose_spell updates _prev_human_pos / _prev_human_time internally
        summon_idx = self._choose_summon_spell(now)
        if summon_idx is not None:
            spell = SPELL_DEFS[summon_idx]
            self.ai_wizard.mana -= spell["mana"]
            self.ai_wizard.spell_cooldowns[summon_idx] = now
            if self.sound_manager is not None:
                self.sound_manager.play_spell(spell["name"])
            return create_summon_effect(ai, human, spell, arena_rect)

        spell_idx = self._choose_spell(human, now)
        if spell_idx is not None:
            spell = SPELL_DEFS[spell_idx]
            # Lead-aim toward predicted human position
            tx, ty = _lead_target(ai, human, spell["speed"], human_vel)
            ax, ay = ai.center
            dist = math.hypot(tx - ax, ty - ay) or 1
            proj_dx = (tx - ax) / dist * spell["speed"]
            proj_dy = (ty - ay) / dist * spell["speed"]
            # Deduct mana and set cooldown
            ai.mana -= spell["mana"]
            ai.spell_cooldowns[spell_idx] = now
            if self.sound_manager is not None:
                self.sound_manager.play_spell(spell["name"])
            return Projectile(ax, ay, proj_dx, proj_dy, ai, spell, target=human)

        return None
