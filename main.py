import pygame
import sys
from player import Player
from arena import Arena
from spells import SPELL_DEFS

SCREEN_W, SCREEN_H = 960, 620
PANEL_W = 150          # side panel width for each player's spell list
FPS = 60
BG_COLOR = (20, 20, 30)


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


def draw_spell_panel(surface, player, panel_x, panel_y, font, font_small, now):
    """Draw a vertical spell list panel for one player."""
    slot_w, slot_h, gap = PANEL_W - 10, 34, 4
    label_col = player.color

    # Player name + stats header
    name_surf = font.render(player.name, True, label_col)
    surface.blit(name_surf, (panel_x + 5, panel_y))

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
        label = spell["name"] + (" [D]" if spell["type"] == "instant" else "")
        surface.blit(font_small.render(label, True, nc), (panel_x + 22, sy + 4))
        mc = (180, 60, 60) if no_mana else (100, 100, 220)
        surface.blit(font_small.render(f"{spell['mana']}mp", True, mc), (panel_x + 22, sy + 18))

        # cooldown overlay
        if on_cd:
            ratio = cd_left / spell["cooldown"]
            cd_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            cd_surf.fill((0, 0, 0, int(150 * ratio)))
            surface.blit(cd_surf, (panel_x + 5, sy))


def draw_hud(surface, p1, p2, font, font_small, now):
    # Left panel — P1
    draw_spell_panel(surface, p1, 0, 10, font, font_small, now)

    # Right panel — P2
    draw_spell_panel(surface, p2, SCREEN_W - PANEL_W, 10, font, font_small, now)

    # Controls hint at very bottom center
    hint = font_small.render(
        "P1: WASD | Q/E spell | SPACE cast        P2: Arrows | ,/. spell | ENTER cast",
        True, (90, 90, 110)
    )
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 16))


def draw_winner(surface, winner, font_big):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    msg = font_big.render(f"{winner} Wins!", True, (255, 220, 50))
    sub = pygame.font.SysFont(None, 30).render("Press R to restart  |  Q to quit", True, (200, 200, 200))
    surface.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30)))
    surface.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Arena RPG — Wizard Duel")
    clock = pygame.time.Clock()

    font       = pygame.font.SysFont(None, 26)
    font_big   = pygame.font.SysFont(None, 64)
    font_small = pygame.font.SysFont(None, 20)

    arena = Arena(SCREEN_W, SCREEN_H, margin=60, left_margin=PANEL_W + 10, right_margin=PANEL_W + 10)
    p1, p2 = make_players(arena)
    projectiles = []
    winner = None

    while True:
        dt  = clock.tick(FPS)
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and winner:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_r and winner:
                    p1, p2 = make_players(arena)
                    projectiles.clear()
                    winner = None
                if not winner:
                    p1.handle_spell_switch(event)
                    p2.handle_spell_switch(event)

        if not winner:
            p1.handle_input(keys, arena.rect)
            p2.handle_input(keys, arena.rect)

            proj = p1.try_cast(keys, now, p2, projectiles, arena.rect)
            if proj:
                projectiles.append(proj)
            proj = p2.try_cast(keys, now, p1, projectiles, arena.rect)
            if proj:
                projectiles.append(proj)

            # Update projectiles
            for p in projectiles:
                p.update(dt, arena.rect)
                if p.owner is p1 and p.check_hit(p2):
                    p.apply(p2)
                elif p.owner is p2 and p.check_hit(p1):
                    p.apply(p1)
            projectiles = [p for p in projectiles if p.alive]

            p1.update(dt)
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
        p1.draw(screen)
        p2.draw(screen)
        draw_hud(screen, p1, p2, font, font_small, now)

        if winner:
            draw_winner(screen, winner, font_big)

        pygame.display.flip()


if __name__ == "__main__":
    main()
