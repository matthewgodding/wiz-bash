"""
Menu screens for Wiz Bash.
Provides mode selection (1P / 2P) and difficulty selection screens.
"""

import sys
import pygame
from ai_controller import EASY, MEDIUM, HARD, DifficultyConfig

SCREEN_W, SCREEN_H = 960, 620
BG_COLOR = (20, 20, 30)
BTN_COLOR = (50, 50, 80)
BTN_HOVER_COLOR = (80, 80, 130)
BTN_BORDER_COLOR = (120, 100, 200)
TEXT_COLOR = (235, 235, 235)
TITLE_COLOR = (255, 220, 50)


def _draw_button(surface, rect, label, font, hovered=False):
    color = BTN_HOVER_COLOR if hovered else BTN_COLOR
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, BTN_BORDER_COLOR, rect, 2, border_radius=8)
    text = font.render(label, True, TEXT_COLOR)
    surface.blit(text, text.get_rect(center=rect.center))


def show_mode_select(screen, fonts) -> str:
    """Runs an event loop until the player clicks a mode button.

    Returns:
        "1p" if "1 Player" is chosen, "2p" if "2 Players" is chosen.
    """
    font = fonts["font"] if "font" in fonts else pygame.font.SysFont(None, 26)
    font_big = fonts["font_big"] if "font_big" in fonts else pygame.font.SysFont(None, 64)

    btn_w, btn_h = 260, 60
    btn_1p = pygame.Rect(SCREEN_W // 2 - btn_w // 2, SCREEN_H // 2 - 10, btn_w, btn_h)
    btn_2p = pygame.Rect(SCREEN_W // 2 - btn_w // 2, SCREEN_H // 2 + 80, btn_w, btn_h)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_1p.collidepoint(event.pos):
                    return "1p"
                if btn_2p.collidepoint(event.pos):
                    return "2p"

        screen.fill(BG_COLOR)

        title = font_big.render("Wiz Bash", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 120)))

        subtitle = font.render("Select Mode", True, (180, 180, 200))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 50)))

        _draw_button(screen, btn_1p, "1 Player", font, btn_1p.collidepoint(mouse_pos))
        _draw_button(screen, btn_2p, "2 Players", font, btn_2p.collidepoint(mouse_pos))

        pygame.display.flip()


def show_difficulty_select(screen, fonts) -> DifficultyConfig:
    """Runs an event loop until the player clicks a difficulty button.

    Returns:
        EASY, MEDIUM, or HARD DifficultyConfig constant.
    """
    font = fonts["font"] if "font" in fonts else pygame.font.SysFont(None, 26)
    font_big = fonts["font_big"] if "font_big" in fonts else pygame.font.SysFont(None, 64)

    btn_w, btn_h = 260, 60
    gap = 20
    total_h = 3 * btn_h + 2 * gap
    start_y = SCREEN_H // 2 - total_h // 2 + 30

    btn_easy   = pygame.Rect(SCREEN_W // 2 - btn_w // 2, start_y,                    btn_w, btn_h)
    btn_medium = pygame.Rect(SCREEN_W // 2 - btn_w // 2, start_y + btn_h + gap,      btn_w, btn_h)
    btn_hard   = pygame.Rect(SCREEN_W // 2 - btn_w // 2, start_y + 2 * (btn_h + gap), btn_w, btn_h)

    buttons = [
        (btn_easy,   "Easy",   EASY),
        (btn_medium, "Medium", MEDIUM),
        (btn_hard,   "Hard",   HARD),
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, _, config in buttons:
                    if rect.collidepoint(event.pos):
                        return config

        screen.fill(BG_COLOR)

        title = font_big.render("Select Difficulty", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 140)))

        for rect, label, _ in buttons:
            _draw_button(screen, rect, label, font, rect.collidepoint(mouse_pos))

        pygame.display.flip()
