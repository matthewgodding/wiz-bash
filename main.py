import pygame
import sys
from player import Player
from arena import Arena
from spells import SPELL_DEFS, Projectile
from audio_manager import SoundManager
from menu import (
    show_mode_select,
    show_difficulty_select,
    show_controller_assignment,
    show_single_player_control_select,
)
from ai_controller import AIController
from input_manager import InputManager

SCREEN_W, SCREEN_H = 960, 620
PANEL_W = 150          # side panel width for each player's spell list
FPS = 60
BG_COLOR = (20, 20, 30)
MAX_SUMMONS_PER_PLAYER = 3


def make_players(arena):
    p1 = Player(
        name="P1", x=arena.rect.left + 60, y=arena.rect.centery - 20,
        color=(70, 130, 220),
        controls={
            "up": pygame.K_w, "down": pygame.K_s,
            "left": pygame.K_a, "right": pygame.K_d,
            "cast": pygame.K_SPACE,
            "spell_next": pygame.K_e, "spell_prev": pygame.K_q,
        },
    )
    p2 = Player(
        name="P2", x=arena.rect.right - 100, y=arena.rect.centery - 20,
        color=(220, 80, 80),
        controls={
            "up": pygame.K_UP, "down": pygame.K_DOWN,
            "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
            "cast": pygame.K_RETURN,
            "spell_next": pygame.K_PERIOD, "spell_prev": pygame.K_COMMA,
        },
    )
    return p1, p2


def draw_spell_panel(surface, player, panel_x, panel_y, font, font_small, now,
                     label_override=None, subtitle=None):
    """Draw a vertical spell list panel for one player."""
    slot_w, slot_h, gap = PANEL_W - 10, 34, 4
    label_col = player.color

    # Player name + stats header
    label = label_override if label_override is not None else player.name
    name_surf = font.render(label, True, label_col)
    surface.blit(name_surf, (panel_x + 5, panel_y))

    if subtitle is not None:
        sub_surf = font_small.render(subtitle, True, (160, 160, 180))
        surface.blit(sub_surf, (panel_x + 5, panel_y + 14))

    hp_surf  = font_small.render(f"HP  {int(player.hp)}/{player.max_hp}", True, (0, 200, 0))
    mp_surf  = font_small.render(f"MP  {int(player.mana)}/{player.max_mana}", True, (80, 120, 255))
    surface.blit(hp_surf,  (panel_x + 5, panel_y + 20))
    surface.blit(mp_surf,  (panel_x + 5, panel_y + 34))

    # HP / mana mini bars
    bw = slot_w
    pygame.draw.rect(surface, (60, 0, 0),   (panel_x + 5, panel_y + 50, bw, 5))
    pygame.draw.rect(surface, (0, 200, 0),  (panel_x + 5, panel_y + 50, int(bw * player.hp / player.max_hp), 5))
    pygame.draw.rect(surface, (0, 0, 60),   (panel_x + 5, panel_y + 57, bw, 5))
    pygame.draw.rect(surface, (60, 80, 255),(panel_x + 5, panel_y + 57, int(bw * player.mana / player.max_mana), 5))

    # Spell slots
    spell_start_y = panel_y + 70
    for i, spell in enumerate(SPELL_DEFS):
        sy = spell_start_y + i * (slot_h + gap)
        selected   = i == player.selected_spell
        cd_left    = max(0, spell["cooldown"] - (now - player.spell_cooldowns[i]))
        on_cd      = cd_left > 0
        no_mana    = player.mana < spell["mana"]

        bg = (70, 55, 110) if selected else (40, 40, 65)
        pygame.draw.rect(surface, bg, (panel_x + 5, sy, slot_w, slot_h), border_radius=4)
        if selected:
            pygame.draw.rect(surface, spell["color"], (panel_x + 5, sy, slot_w, slot_h), 2, border_radius=4)

        # color dot
        pygame.draw.circle(surface, spell["color"], (panel_x + 14, sy + slot_h // 2), 5)

        # name + cost + type tag
        nc = (170, 170, 170) if (on_cd or no_mana) else (235, 235, 235)
        tag = ""
        if spell["type"] == "instant":
            tag = " [D]"
        elif spell["type"] == "summon":
            tag = " [S]"
        label = spell["name"] + tag
        surface.blit(font_small.render(label, True, nc), (panel_x + 22, sy + 4))
        mc = (180, 60, 60) if no_mana else (100, 100, 220)
        surface.blit(font_small.render(f"{spell['mana']}mp", True, mc), (panel_x + 22, sy + 18))

        # cooldown overlay
        if on_cd:
            ratio = cd_left / spell["cooldown"]
            cd_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            cd_surf.fill((0, 0, 0, int(150 * ratio)))
            surface.blit(cd_surf, (panel_x + 5, sy))


def draw_hud(surface, p1, p2, font, font_small, now, mode="2p", difficulty=None, input_manager=None, summon_counts=None):
    # Left panel — P1
    p1_label = p1.name
    if input_manager is not None and input_manager.get_assigned_controller(0) is not None:
        p1_label = f"{p1.name} (PAD)"
    p1_sub = f"Summons {summon_counts.get(0, 0)}" if summon_counts is not None else None
    draw_spell_panel(surface, p1, 0, 10, font, font_small, now, label_override=p1_label, subtitle=p1_sub)

    # Right panel — P2 (or CPU in 1p mode)
    if mode == "1p":
        subtitle = difficulty.name if difficulty is not None else None
        if summon_counts is not None:
            subtitle = f"{subtitle or 'CPU'} | Summons {summon_counts.get(1, 0)}"
        draw_spell_panel(surface, p2, SCREEN_W - PANEL_W, 10, font, font_small, now,
                         label_override="CPU", subtitle=subtitle)
    else:
        p2_label = p2.name
        if input_manager is not None and input_manager.get_assigned_controller(1) is not None:
            p2_label = f"{p2.name} (PAD)"
        p2_sub = f"Summons {summon_counts.get(1, 0)}" if summon_counts is not None else None
        draw_spell_panel(surface, p2, SCREEN_W - PANEL_W, 10, font, font_small, now, label_override=p2_label, subtitle=p2_sub)

    # Controls hint at very bottom center
    if mode == "1p":
        hint = font_small.render(
            "P1: WASD | Q/E spell | SPACE cast",
            True, (90, 90, 110)
        )
    else:
        hint = font_small.render(
            "P1: WASD | Q/E spell | SPACE cast        P2: Arrows | ,/. spell | ENTER cast",
            True, (90, 90, 110)
        )
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 16))


def draw_winner(surface, winner, font_big, mode="2p", p1_name="P1"):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    if mode == "1p":
        text = "You Win!" if winner == p1_name else "CPU Wins!"
    else:
        text = f"{winner} Wins!"
    msg = font_big.render(text, True, (255, 220, 50))
    sub = pygame.font.SysFont(None, 30).render("Press R to restart  |  Q to quit", True, (200, 200, 200))
    surface.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30)))
    surface.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20)))


def run_game(screen, clock, fonts, arena, mode, input_manager, difficulty=None, sound_manager=None):
    """
    Runs a single match. Returns when the match ends (winner determined and R pressed).
    mode: "1p" or "2p"
    difficulty: DifficultyConfig or None (only used when mode == "1p")
    """
    font       = fonts["font"]
    font_big   = fonts["font_big"]
    font_small = fonts["font_small"]

    p1, p2 = make_players(arena)
    input_manager.set_player_keyboard_controls(0, p1.controls)
    input_manager.set_player_keyboard_controls(1, p2.controls)
    input_manager.auto_assign_for_mode(mode)
    projectiles = []
    summons = []
    winner = None

    ai_controller = None
    if mode == "1p":
        ai_controller = AIController(p2, difficulty, sound_manager=sound_manager)

    while True:
        dt  = clock.tick(FPS)
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            input_manager.process_event(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and winner:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and winner:
                    # Return to mode select — let main() loop handle it
                    return
                if not winner:
                    p1.handle_spell_switch(event)
                    if mode == "2p":
                        p2.handle_spell_switch(event)

        if not winner:
            p1_actions = input_manager.get_actions(0, keys)
            p2_actions = input_manager.get_actions(1, keys)

            p1.handle_spell_switch_action(p1_actions)
            if mode == "2p":
                p2.handle_spell_switch_action(p2_actions)

            p1.handle_input(keys, arena.rect, actions=p1_actions)

            if mode == "2p":
                p2.handle_input(keys, arena.rect, actions=p2_actions)
                proj = p2.try_cast(keys, now, p1, projectiles, arena.rect, actions=p2_actions, sound_manager=sound_manager)
                if proj:
                    if isinstance(proj, Projectile):
                        projectiles.append(proj)
                    elif sum(1 for s in summons if s.owner is p2 and s.alive) < MAX_SUMMONS_PER_PLAYER:
                        summons.append(proj)
            else:
                # 1p mode: AI drives p2
                proj = ai_controller.update(now, dt, p1, projectiles, arena.rect)
                if proj is not None:
                    if isinstance(proj, Projectile):
                        projectiles.append(proj)
                    elif sum(1 for s in summons if s.owner is p2 and s.alive) < MAX_SUMMONS_PER_PLAYER:
                        summons.append(proj)
                # p2 still needs status effect updates
                p2.update(dt)

            proj = p1.try_cast(keys, now, p2, projectiles, arena.rect, actions=p1_actions, sound_manager=sound_manager)
            if proj:
                if isinstance(proj, Projectile):
                    projectiles.append(proj)
                elif sum(1 for s in summons if s.owner is p1 and s.alive) < MAX_SUMMONS_PER_PLAYER:
                    summons.append(proj)

            p1_summons = [s for s in summons if s.owner is p1 and s.alive]
            p2_summons = [s for s in summons if s.owner is p2 and s.alive]
            for summon in summons:
                if not summon.alive:
                    continue
                if summon.owner is p1:
                    summon.update(dt, arena.rect, p2, p2_summons, projectiles)
                else:
                    summon.update(dt, arena.rect, p1, p1_summons, projectiles)

            # Update projectiles
            for p in projectiles:
                p.update(dt, arena.rect)
                if p.owner is p1 and p.check_hit(p2):
                    p.apply(p2)
                elif p.owner is p2 and p.check_hit(p1):
                    p.apply(p1)
                elif p.owner is p1:
                    for summon in p2_summons:
                        if summon.alive and summon.collides_with_projectile(p):
                            p.apply(summon)
                            break
                elif p.owner is p2:
                    for summon in p1_summons:
                        if summon.alive and summon.collides_with_projectile(p):
                            p.apply(summon)
                            break
            projectiles = [p for p in projectiles if p.alive]
            summons = [s for s in summons if s.alive]

            p1.update(dt)
            if mode == "2p":
                p2.update(dt)

            if not p2.is_alive():
                winner = p1.name
            elif not p1.is_alive():
                winner = p2.name

        # Draw
        screen.fill(BG_COLOR)
        arena.draw(screen)
        for p in projectiles:
            p.draw(screen)
        for summon in summons:
            summon.draw(screen)
        p1.draw(screen)
        p2.draw(screen)
        summon_counts = {
            0: sum(1 for s in summons if s.owner is p1 and s.alive),
            1: sum(1 for s in summons if s.owner is p2 and s.alive),
        }
        draw_hud(
            screen,
            p1,
            p2,
            font,
            font_small,
            now,
            mode=mode,
            difficulty=difficulty,
            input_manager=input_manager,
            summon_counts=summon_counts,
        )

        if winner:
            draw_winner(screen, winner, font_big, mode=mode, p1_name=p1.name)

        pygame.display.flip()


def main():
    pygame.init()
    sound_manager = SoundManager()
    input_manager = InputManager()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Arena RPG — Wizard Duel")
    clock = pygame.time.Clock()

    fonts = {
        "font":       pygame.font.SysFont(None, 26),
        "font_big":   pygame.font.SysFont(None, 64),
        "font_small": pygame.font.SysFont(None, 20),
    }

    arena = Arena(SCREEN_W, SCREEN_H, margin=60, left_margin=PANEL_W + 10, right_margin=PANEL_W + 10)

    while True:
        mode = show_mode_select(screen, fonts, input_manager=input_manager)
        input_manager.auto_assign_for_mode(mode)
        if mode == "2p" and input_manager.has_any_controller():
            show_controller_assignment(screen, fonts, input_manager)
            input_manager.auto_assign_for_mode(mode)
        difficulty = None
        if mode == "1p":
            if input_manager.has_any_controller():
                selected_controller = show_single_player_control_select(screen, fonts, input_manager)
                input_manager.unassign_player(0)
                if selected_controller is not None:
                    input_manager.assign_controller(0, selected_controller)
            difficulty = show_difficulty_select(screen, fonts, input_manager=input_manager)
        run_game(screen, clock, fonts, arena, mode, input_manager, difficulty, sound_manager)
        # After run_game returns, loop back to show_mode_select


if __name__ == "__main__":
    main()
