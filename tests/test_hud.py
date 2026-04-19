"""
Unit tests for HUD and victory message rendering in main.py.
Tests Requirements: 7.1, 7.2, 7.3, 7.4
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from main import draw_spell_panel, draw_hud, draw_winner, SCREEN_W, SCREEN_H, PANEL_W
from ai_controller import EASY, MEDIUM, HARD


def _make_font():
    """Return a mock font whose render() returns a surface-like mock."""
    font = MagicMock()
    surf = MagicMock()
    surf.get_rect.return_value = MagicMock(center=(0, 0))
    surf.get_width.return_value = 100
    font.render.return_value = surf
    return font


def _make_player(name="P1", color=(70, 130, 220)):
    """Return a minimal mock Player with correct spell_cooldowns length."""
    from spells import SPELL_DEFS
    player = MagicMock()
    player.name = name
    player.color = color
    player.hp = 80
    player.max_hp = 100
    player.mana = 60
    player.max_mana = 100
    player.selected_spell = 0
    player.spell_cooldowns = [0] * len(SPELL_DEFS)
    return player


def _draw_spell_panel_patched(surface, player, font, font_small, **kwargs):
    """Call draw_spell_panel with pygame.draw patched out."""
    with patch("pygame.draw.rect"), patch("pygame.draw.circle"), \
         patch("pygame.Surface") as mock_surf_cls:
        mock_surf_cls.return_value = MagicMock()
        draw_spell_panel(surface, player, 0, 10, font, font_small, now=0, **kwargs)


class TestDrawSpellPanelLabelOverride(unittest.TestCase):
    """Requirement 7.1 — AI panel shows 'CPU' label when label_override is passed."""

    def setUp(self):
        self.surface = MagicMock()
        self.font = _make_font()
        self.font_small = _make_font()
        self.player = _make_player(name="P2")

    def _rendered_strings(self, font_mock):
        """Collect all string arguments passed to font.render()."""
        return [c.args[0] for c in font_mock.render.call_args_list]

    def test_label_override_cpu_is_rendered(self):
        """When label_override='CPU', the panel header should show 'CPU'."""
        _draw_spell_panel_patched(self.surface, self.player,
                                  self.font, self.font_small,
                                  label_override="CPU")
        rendered = self._rendered_strings(self.font)
        self.assertIn("CPU", rendered)

    def test_label_override_replaces_player_name(self):
        """When label_override='CPU', the player's real name should NOT appear in the header font."""
        _draw_spell_panel_patched(self.surface, self.player,
                                  self.font, self.font_small,
                                  label_override="CPU")
        rendered = self._rendered_strings(self.font)
        self.assertNotIn("P2", rendered)

    def test_no_label_override_uses_player_name(self):
        """Without label_override, the player's name should be rendered."""
        _draw_spell_panel_patched(self.surface, self.player,
                                  self.font, self.font_small)
        rendered = self._rendered_strings(self.font)
        self.assertIn("P2", rendered)

    def test_subtitle_is_rendered_when_provided(self):
        """When subtitle='Easy' is passed, it should be rendered via font_small."""
        _draw_spell_panel_patched(self.surface, self.player,
                                  self.font, self.font_small,
                                  label_override="CPU", subtitle="Easy")
        rendered_small = self._rendered_strings(self.font_small)
        self.assertIn("Easy", rendered_small)

    def test_no_subtitle_when_not_provided(self):
        """Without subtitle, 'Easy'/'Medium'/'Hard' should not appear in font_small renders."""
        _draw_spell_panel_patched(self.surface, self.player,
                                  self.font, self.font_small)
        rendered_small = self._rendered_strings(self.font_small)
        for diff_name in ("Easy", "Medium", "Hard"):
            self.assertNotIn(diff_name, rendered_small)


class TestDrawHudMode(unittest.TestCase):
    """Requirements 7.1, 7.2 — draw_hud passes correct overrides and hides P2 hints in 1p mode."""

    def setUp(self):
        self.surface = MagicMock()
        self.font = _make_font()
        self.font_small = _make_font()
        self.p1 = _make_player(name="P1")
        self.p2 = _make_player(name="P2", color=(220, 80, 80))

    def _call_draw_hud(self, **kwargs):
        with patch("pygame.draw.rect"), patch("pygame.draw.circle"), \
             patch("pygame.Surface") as mock_surf_cls:
            mock_surf_cls.return_value = MagicMock()
            draw_hud(self.surface, self.p1, self.p2,
                     self.font, self.font_small, now=0, **kwargs)

    def _all_rendered_strings(self):
        """Collect all strings rendered by font and font_small."""
        strings = []
        for c in self.font.render.call_args_list:
            strings.append(c.args[0])
        for c in self.font_small.render.call_args_list:
            strings.append(c.args[0])
        return strings

    def test_1p_mode_renders_cpu_label(self):
        """In 1p mode, the AI panel header should say 'CPU'."""
        self._call_draw_hud(mode="1p", difficulty=EASY)
        self.assertIn("CPU", self._all_rendered_strings())

    def test_1p_mode_renders_difficulty_name(self):
        """In 1p mode, the difficulty name should appear as subtitle."""
        self._call_draw_hud(mode="1p", difficulty=EASY)
        self.assertIn("Easy", self._all_rendered_strings())

    def test_1p_mode_hides_p2_control_hints(self):
        """In 1p mode, P2 control hints should not appear in the hint bar."""
        self._call_draw_hud(mode="1p", difficulty=EASY)
        hint_strings = [c.args[0] for c in self.font_small.render.call_args_list
                        if "ENTER" in c.args[0] or "Arrows" in c.args[0]]
        self.assertEqual(hint_strings, [],
                         "P2 control hints should not be shown in 1p mode")

    def test_1p_mode_shows_p1_control_hints(self):
        """In 1p mode, P1 control hints should still appear."""
        self._call_draw_hud(mode="1p", difficulty=EASY)
        hint_strings = [c.args[0] for c in self.font_small.render.call_args_list
                        if "WASD" in c.args[0]]
        self.assertGreater(len(hint_strings), 0,
                           "P1 control hints should be shown in 1p mode")

    def test_2p_mode_shows_both_control_hints(self):
        """In 2p mode, both P1 and P2 control hints should appear."""
        self._call_draw_hud(mode="2p")
        hint_strings = [c.args[0] for c in self.font_small.render.call_args_list
                        if "WASD" in c.args[0] and "ENTER" in c.args[0]]
        self.assertGreater(len(hint_strings), 0,
                           "Both P1 and P2 hints should appear in 2p mode")


class TestDrawWinner(unittest.TestCase):
    """Requirements 7.3, 7.4 — victory messages in 1p and 2p modes."""

    def setUp(self):
        self.surface = MagicMock()
        self.font_big = _make_font()

    def _rendered_text(self):
        """Return the first string passed to font_big.render (the victory message)."""
        return self.font_big.render.call_args_list[0].args[0]

    def test_1p_human_wins_shows_you_win(self):
        """In 1p mode, when the human (P1) wins, display 'You Win!'."""
        with patch("pygame.Surface") as mock_surf_cls, \
             patch("pygame.font.SysFont") as mock_sysfont:
            mock_surf_cls.return_value = MagicMock()
            sub_font = _make_font()
            mock_sysfont.return_value = sub_font
            draw_winner(self.surface, winner="P1", font_big=self.font_big,
                        mode="1p", p1_name="P1")
        self.assertEqual(self._rendered_text(), "You Win!")

    def test_1p_ai_wins_shows_cpu_wins(self):
        """In 1p mode, when the AI (P2) wins, display 'CPU Wins!'."""
        with patch("pygame.Surface") as mock_surf_cls, \
             patch("pygame.font.SysFont") as mock_sysfont:
            mock_surf_cls.return_value = MagicMock()
            sub_font = _make_font()
            mock_sysfont.return_value = sub_font
            draw_winner(self.surface, winner="P2", font_big=self.font_big,
                        mode="1p", p1_name="P1")
        self.assertEqual(self._rendered_text(), "CPU Wins!")

    def test_2p_mode_shows_winner_name(self):
        """In 2p mode, display '{winner} Wins!'."""
        with patch("pygame.Surface") as mock_surf_cls, \
             patch("pygame.font.SysFont") as mock_sysfont:
            mock_surf_cls.return_value = MagicMock()
            sub_font = _make_font()
            mock_sysfont.return_value = sub_font
            draw_winner(self.surface, winner="P1", font_big=self.font_big,
                        mode="2p", p1_name="P1")
        self.assertEqual(self._rendered_text(), "P1 Wins!")

    def test_2p_mode_p2_wins_shows_p2_wins(self):
        """In 2p mode, P2 winning shows 'P2 Wins!'."""
        with patch("pygame.Surface") as mock_surf_cls, \
             patch("pygame.font.SysFont") as mock_sysfont:
            mock_surf_cls.return_value = MagicMock()
            sub_font = _make_font()
            mock_sysfont.return_value = sub_font
            draw_winner(self.surface, winner="P2", font_big=self.font_big,
                        mode="2p", p1_name="P1")
        self.assertEqual(self._rendered_text(), "P2 Wins!")


if __name__ == "__main__":
    unittest.main()
