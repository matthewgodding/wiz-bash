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


def _next_menu_index(current, direction, item_count):
    return (current + direction) % item_count


def show_mode_select(screen, fonts, input_manager=None) -> str:
    """Runs an event loop until the player clicks a mode button.

    Returns:
        "1p" if "1 Player" is chosen, "2p" if "2 Players" is chosen.
    """
    font = fonts["font"] if "font" in fonts else pygame.font.SysFont(None, 26)
    font_big = fonts["font_big"] if "font_big" in fonts else pygame.font.SysFont(None, 64)

    btn_w, btn_h = 260, 60
    btn_1p = pygame.Rect(SCREEN_W // 2 - btn_w // 2, SCREEN_H // 2 - 10, btn_w, btn_h)
    btn_2p = pygame.Rect(SCREEN_W // 2 - btn_w // 2, SCREEN_H // 2 + 80, btn_w, btn_h)

    selected_idx = 0
    labels = ("1 Player", "2 Players")
    rects = (btn_1p, btn_2p)
    values = ("1p", "2p")

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if input_manager is not None:
                input_manager.process_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_1p.collidepoint(event.pos):
                    return "1p"
                if btn_2p.collidepoint(event.pos):
                    return "2p"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected_idx = _next_menu_index(selected_idx, -1, len(values))
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected_idx = _next_menu_index(selected_idx, 1, len(values))
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return values[selected_idx]

        if input_manager is not None:
            menu_actions = input_manager.get_menu_actions()
            if menu_actions["up"]:
                selected_idx = _next_menu_index(selected_idx, -1, len(values))
            elif menu_actions["down"]:
                selected_idx = _next_menu_index(selected_idx, 1, len(values))
            if menu_actions["confirm"]:
                return values[selected_idx]

        screen.fill(BG_COLOR)

        title = font_big.render("Wiz Bash", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 120)))

        subtitle = font.render("Select Mode", True, (180, 180, 200))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 50)))

        for idx, rect in enumerate(rects):
            hovered = rect.collidepoint(mouse_pos) or idx == selected_idx
            _draw_button(screen, rect, labels[idx], font, hovered)

        pygame.display.flip()


def show_difficulty_select(screen, fonts, input_manager=None) -> DifficultyConfig:
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

    selected_idx = 0

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if input_manager is not None:
                input_manager.process_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, _, config in buttons:
                    if rect.collidepoint(event.pos):
                        return config
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected_idx = _next_menu_index(selected_idx, -1, len(buttons))
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected_idx = _next_menu_index(selected_idx, 1, len(buttons))
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return buttons[selected_idx][2]

        if input_manager is not None:
            menu_actions = input_manager.get_menu_actions()
            if menu_actions["up"]:
                selected_idx = _next_menu_index(selected_idx, -1, len(buttons))
            elif menu_actions["down"]:
                selected_idx = _next_menu_index(selected_idx, 1, len(buttons))
            if menu_actions["confirm"]:
                return buttons[selected_idx][2]

        screen.fill(BG_COLOR)

        title = font_big.render("Select Difficulty", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 140)))

        for idx, (rect, label, _) in enumerate(buttons):
            hovered = rect.collidepoint(mouse_pos) or idx == selected_idx
            _draw_button(screen, rect, label, font, hovered)

        pygame.display.flip()


def show_controller_assignment(screen, fonts, input_manager):
    """2P assignment screen. Players claim controllers by pressing any button."""
    font = fonts["font"] if "font" in fonts else pygame.font.SysFont(None, 26)
    font_big = fonts["font_big"] if "font_big" in fonts else pygame.font.SysFont(None, 64)

    btn_w, btn_h = 360, 60
    done_btn = pygame.Rect(SCREEN_W // 2 - btn_w // 2, SCREEN_H - 110, btn_w, btn_h)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            input_manager.process_event(event)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and done_btn.collidepoint(event.pos):
                return

            if event.type == pygame.JOYBUTTONDOWN:
                if event.instance_id not in input_manager.player_assignments.values():
                    if input_manager.get_assigned_controller(0) is None:
                        input_manager.assign_controller(0, event.instance_id)
                    elif input_manager.get_assigned_controller(1) is None:
                        input_manager.assign_controller(1, event.instance_id)

        screen.fill(BG_COLOR)
        title = font_big.render("Controller Assignment", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 110)))

        subtitle = font.render("Press any controller button to claim a player slot", True, (180, 180, 200))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 165)))

        p1_assigned = input_manager.get_assigned_controller(0)
        p2_assigned = input_manager.get_assigned_controller(1)
        p1_label = input_manager.get_controller_display(p1_assigned) if p1_assigned is not None else "Keyboard"
        p2_label = input_manager.get_controller_display(p2_assigned) if p2_assigned is not None else "Keyboard"
        p1_text = font.render(f"Player 1: {p1_label}", True, TEXT_COLOR)
        p2_text = font.render(f"Player 2: {p2_label}", True, TEXT_COLOR)
        screen.blit(p1_text, p1_text.get_rect(center=(SCREEN_W // 2, 260)))
        screen.blit(p2_text, p2_text.get_rect(center=(SCREEN_W // 2, 310)))

        connected = sorted(input_manager.controllers.keys())
        if connected:
            heading = font.render("Connected Controllers:", True, (180, 180, 200))
            screen.blit(heading, heading.get_rect(center=(SCREEN_W // 2, 380)))
            for idx, instance_id in enumerate(connected):
                owner = None
                if input_manager.get_assigned_controller(0) == instance_id:
                    owner = "P1"
                elif input_manager.get_assigned_controller(1) == instance_id:
                    owner = "P2"
                suffix = f" -> {owner}" if owner else " -> unassigned"
                label = input_manager.get_controller_display(instance_id) + suffix
                item = font.render(label, True, TEXT_COLOR)
                screen.blit(item, item.get_rect(center=(SCREEN_W // 2, 410 + idx * 28)))

        _draw_button(screen, done_btn, "Continue", font, done_btn.collidepoint(mouse_pos))
        help_text = font.render("Enter / Space to continue", True, (140, 140, 170))
        screen.blit(help_text, help_text.get_rect(center=(SCREEN_W // 2, SCREEN_H - 35)))
        pygame.display.flip()
