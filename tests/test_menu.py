"""
Unit tests for menu.py — mode select and difficulty select screens.
Tests Requirements: 1.1, 1.2, 1.3, 2.1, 2.3, 2.4
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from ai_controller import EASY, MEDIUM, HARD, DifficultyConfig
from menu import show_mode_select, show_difficulty_select, SCREEN_W, SCREEN_H


def _make_click_event(x, y):
    """Return a fake MOUSEBUTTONDOWN event at (x, y)."""
    event = MagicMock()
    event.type = pygame.MOUSEBUTTONDOWN
    event.button = 1
    event.pos = (x, y)
    return event


def _make_fonts():
    """Return a minimal fonts dict (no real pygame display needed for logic tests)."""
    font = MagicMock()
    # render() must return a surface-like object with get_rect() and get_width()
    surf = MagicMock()
    surf.get_rect.return_value = MagicMock(center=(0, 0))
    surf.get_width.return_value = 100
    font.render.return_value = surf
    return {"font": font, "font_big": font, "font_small": font}


class TestDifficultyConfigPresets(unittest.TestCase):
    """Verify the exact preset values — no pygame needed."""

    def test_easy_preset_values(self):
        self.assertEqual(EASY.name, "Easy")
        self.assertEqual(EASY.reaction_delay, 800)
        self.assertAlmostEqual(EASY.cast_accuracy, 0.60)
        self.assertAlmostEqual(EASY.ignore_threat_prob, 0.40)
        self.assertTrue(EASY.random_spell_select)

    def test_medium_preset_values(self):
        self.assertEqual(MEDIUM.name, "Medium")
        self.assertEqual(MEDIUM.reaction_delay, 400)
        self.assertAlmostEqual(MEDIUM.cast_accuracy, 0.85)
        self.assertAlmostEqual(MEDIUM.ignore_threat_prob, 0.00)
        self.assertFalse(MEDIUM.random_spell_select)

    def test_hard_preset_values(self):
        self.assertEqual(HARD.name, "Hard")
        self.assertEqual(HARD.reaction_delay, 100)
        self.assertAlmostEqual(HARD.cast_accuracy, 1.00)
        self.assertAlmostEqual(HARD.ignore_threat_prob, 0.00)
        self.assertFalse(HARD.random_spell_select)

    def test_presets_are_difficulty_config_instances(self):
        for preset in (EASY, MEDIUM, HARD):
            self.assertIsInstance(preset, DifficultyConfig)


class TestShowModeSelect(unittest.TestCase):
    """Test show_mode_select returns correct values on button click."""

    def _run_with_click(self, click_x, click_y):
        """Patch pygame internals and simulate a single click at (click_x, click_y)."""
        click_event = _make_click_event(click_x, click_y)
        fonts = _make_fonts()

        screen = MagicMock()
        screen.fill = MagicMock()
        screen.blit = MagicMock()

        surf = MagicMock()
        surf.get_rect.return_value = MagicMock(center=(0, 0))

        with patch("pygame.event.get", side_effect=[[click_event]]), \
             patch("pygame.mouse.get_pos", return_value=(click_x, click_y)), \
             patch("pygame.display.flip"), \
             patch("pygame.draw.rect"), \
             patch("pygame.quit"), \
             patch("sys.exit"):
            result = show_mode_select(screen, fonts)
        return result

    def test_click_1player_button_returns_1p(self):
        # "1 Player" button is centered at SCREEN_W//2, SCREEN_H//2 - 10 + 30 = SCREEN_H//2 + 20
        btn_center_x = SCREEN_W // 2
        btn_center_y = SCREEN_H // 2 - 10 + 30  # rect.y + btn_h//2
        result = self._run_with_click(btn_center_x, btn_center_y)
        self.assertEqual(result, "1p")

    def test_click_2players_button_returns_2p(self):
        # "2 Players" button is at SCREEN_H//2 + 80 + 30
        btn_center_x = SCREEN_W // 2
        btn_center_y = SCREEN_H // 2 + 80 + 30
        result = self._run_with_click(btn_center_x, btn_center_y)
        self.assertEqual(result, "2p")

    def test_return_value_is_string(self):
        btn_center_x = SCREEN_W // 2
        btn_center_y = SCREEN_H // 2 - 10 + 30
        result = self._run_with_click(btn_center_x, btn_center_y)
        self.assertIsInstance(result, str)


class TestShowDifficultySelect(unittest.TestCase):
    """Test show_difficulty_select returns correct DifficultyConfig on button click."""

    def _btn_center_y(self, index):
        """Compute the vertical center of button at position `index` (0=Easy, 1=Medium, 2=Hard)."""
        btn_h, gap = 60, 20
        total_h = 3 * btn_h + 2 * gap
        start_y = SCREEN_H // 2 - total_h // 2 + 30
        return start_y + index * (btn_h + gap) + btn_h // 2

    def _run_with_click(self, click_x, click_y):
        click_event = _make_click_event(click_x, click_y)
        fonts = _make_fonts()

        screen = MagicMock()
        screen.fill = MagicMock()
        screen.blit = MagicMock()

        with patch("pygame.event.get", side_effect=[[click_event]]), \
             patch("pygame.mouse.get_pos", return_value=(click_x, click_y)), \
             patch("pygame.display.flip"), \
             patch("pygame.draw.rect"), \
             patch("pygame.quit"), \
             patch("sys.exit"):
            result = show_difficulty_select(screen, fonts)
        return result

    def test_click_easy_returns_easy_config(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(0))
        self.assertIs(result, EASY)

    def test_click_medium_returns_medium_config(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(1))
        self.assertIs(result, MEDIUM)

    def test_click_hard_returns_hard_config(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(2))
        self.assertIs(result, HARD)

    def test_easy_result_has_correct_reaction_delay(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(0))
        self.assertEqual(result.reaction_delay, 800)

    def test_medium_result_has_correct_reaction_delay(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(1))
        self.assertEqual(result.reaction_delay, 400)

    def test_hard_result_has_correct_reaction_delay(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(2))
        self.assertEqual(result.reaction_delay, 100)

    def test_return_value_is_difficulty_config(self):
        result = self._run_with_click(SCREEN_W // 2, self._btn_center_y(0))
        self.assertIsInstance(result, DifficultyConfig)


if __name__ == "__main__":
    unittest.main()
