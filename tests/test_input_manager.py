"""
Focused unit tests for InputManager controller support behavior.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from input_manager import InputManager


def _make_key_state(*pressed):
    keys = [False] * 1024
    for key in pressed:
        keys[key] = True
    return keys


class FakeJoystick:
    def __init__(self, instance_id, axes=None, hat=(0, 0), buttons=None, fail_axis=False):
        self._instance_id = instance_id
        self._axes = axes if axes is not None else [0.0, 0.0]
        self._hat = hat
        self._buttons = buttons if buttons is not None else {}
        self._fail_axis = fail_axis

    def init(self):
        return None

    def get_instance_id(self):
        return self._instance_id

    def get_numaxes(self):
        return len(self._axes)

    def get_axis(self, index):
        if self._fail_axis:
            raise pygame.error("axis read failed")
        return self._axes[index]

    def get_numhats(self):
        return 1

    def get_hat(self, _index):
        return self._hat

    def get_numbuttons(self):
        if not self._buttons:
            return 0
        return max(self._buttons.keys()) + 1

    def get_button(self, index):
        return int(bool(self._buttons.get(index, False)))


class TestInputManager(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(InputManager, "_init_joysticks", lambda _self: None)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.manager = InputManager()
        self.controls = {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "cast": pygame.K_SPACE,
            "spell_next": pygame.K_e,
            "spell_prev": pygame.K_q,
        }
        self.manager.set_player_keyboard_controls(0, self.controls)

    def test_dead_zone_ignores_small_axes(self):
        self.manager.controllers[10] = FakeJoystick(10, axes=[0.1, -0.15])
        self.manager.player_assignments[0] = 10
        actions = self.manager.get_actions(0, _make_key_state())
        self.assertFalse(actions["up"])
        self.assertFalse(actions["down"])
        self.assertFalse(actions["left"])
        self.assertFalse(actions["right"])

    def test_controller_mapping_axes_hat_and_buttons(self):
        self.manager.controllers[11] = FakeJoystick(
            11,
            axes=[-0.8, 0.9],
            hat=(1, 0),
            buttons={0: True, 4: True, 5: True},
        )
        self.manager.player_assignments[0] = 11
        actions = self.manager.get_actions(0, _make_key_state())
        self.assertTrue(actions["left"])
        self.assertTrue(actions["down"])
        self.assertTrue(actions["right"])  # from d-pad hat
        self.assertTrue(actions["cast"])
        self.assertTrue(actions["spell_next"])
        self.assertTrue(actions["spell_prev"])

    def test_spell_buttons_are_edge_triggered(self):
        self.manager.controllers[12] = FakeJoystick(12, buttons={5: True})
        self.manager.player_assignments[0] = 12
        first = self.manager.get_actions(0, _make_key_state())
        second = self.manager.get_actions(0, _make_key_state())
        self.assertTrue(first["spell_next"])
        self.assertFalse(second["spell_next"])

    def test_keyboard_and_controller_actions_merge(self):
        self.manager.controllers[13] = FakeJoystick(13, axes=[0.9, 0.0], buttons={0: True})
        self.manager.player_assignments[0] = 13
        actions = self.manager.get_actions(0, _make_key_state(pygame.K_w))
        self.assertTrue(actions["up"])      # keyboard
        self.assertTrue(actions["right"])   # controller axis
        self.assertTrue(actions["cast"])    # controller button

    def test_controller_read_error_returns_all_inactive(self):
        self.manager.controllers[14] = FakeJoystick(14, fail_axis=True)
        self.manager.player_assignments[0] = 14
        actions = self.manager.get_actions(0, _make_key_state())
        self.assertTrue(all(not value for value in actions.values()))

    def test_assign_controller_rejects_duplicate_assignment(self):
        self.manager.controllers[21] = FakeJoystick(21)
        ok_first = self.manager.assign_controller(0, 21)
        ok_second = self.manager.assign_controller(1, 21)
        self.assertTrue(ok_first)
        self.assertFalse(ok_second)

    def test_auto_assign_1p_uses_first_available_controller(self):
        self.manager.controllers = {31: FakeJoystick(31), 32: FakeJoystick(32)}
        with patch.object(self.manager, "refresh_controllers", lambda: None):
            self.manager.auto_assign_for_mode("1p")
        self.assertEqual(self.manager.player_assignments[0], 31)
        self.assertIsNone(self.manager.player_assignments[1])

    def test_auto_assign_2p_single_controller_defaults_p1(self):
        self.manager.controllers = {41: FakeJoystick(41)}
        self.manager.player_assignments[0] = None
        self.manager.player_assignments[1] = None
        with patch.object(self.manager, "refresh_controllers", lambda: None):
            self.manager.auto_assign_for_mode("2p")
        self.assertEqual(self.manager.player_assignments[0], 41)
        self.assertIsNone(self.manager.player_assignments[1])

    def test_process_event_add_and_remove_controller(self):
        fake = FakeJoystick(51)
        with patch("pygame.joystick.Joystick", return_value=fake):
            add_event = MagicMock(type=pygame.JOYDEVICEADDED, device_index=0)
            self.manager.process_event(add_event)
        self.assertIn(51, self.manager.controllers)

        self.manager.player_assignments[0] = 51
        remove_event = MagicMock(type=pygame.JOYDEVICEREMOVED, instance_id=51)
        self.manager.process_event(remove_event)
        self.assertNotIn(51, self.manager.controllers)
        self.assertIsNone(self.manager.player_assignments[0])

    def test_menu_actions_support_edge_trigger(self):
        self.manager.controllers[61] = FakeJoystick(61, axes=[0.0, -0.9], buttons={0: True})
        first = self.manager.get_menu_actions()
        second = self.manager.get_menu_actions()
        self.assertTrue(first["up"])
        self.assertTrue(first["confirm"])
        self.assertFalse(second["up"])
        self.assertFalse(second["confirm"])


if __name__ == "__main__":
    unittest.main()
