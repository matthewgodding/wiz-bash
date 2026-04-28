import sys
import pygame


DEFAULT_DEAD_ZONE = 0.2
PLAYER_COUNT = 2
ACTION_NAMES = ("up", "down", "left", "right", "cast", "spell_next", "spell_prev")


class InputManager:
    """Unifies keyboard and controller input into action booleans."""

    def __init__(self, dead_zone=DEFAULT_DEAD_ZONE):
        self.dead_zone = dead_zone
        self.controllers = {}  # instance_id -> joystick
        self.player_assignments = {idx: None for idx in range(PLAYER_COUNT)}
        self.player_keyboard_controls = {}
        self._prev_controller_actions = {
            idx: {"spell_next": False, "spell_prev": False} for idx in range(PLAYER_COUNT)
        }
        self._menu_prev = {"up": False, "down": False, "confirm": False}
        self._init_joysticks()

    def _init_joysticks(self):
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.refresh_controllers()

    def refresh_controllers(self):
        active_ids = set()
        count = pygame.joystick.get_count()
        for index in range(count):
            try:
                joystick = pygame.joystick.Joystick(index)
                joystick.init()
                instance_id = joystick.get_instance_id()
                self.controllers[instance_id] = joystick
                active_ids.add(instance_id)
            except pygame.error as exc:
                print(f"[InputManager] Warning: failed to init controller {index}: {exc}", file=sys.stderr)
        stale = [instance_id for instance_id in self.controllers if instance_id not in active_ids]
        for instance_id in stale:
            self._remove_controller(instance_id)

    def process_event(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            try:
                joystick = pygame.joystick.Joystick(event.device_index)
                joystick.init()
                self.controllers[joystick.get_instance_id()] = joystick
            except pygame.error as exc:
                print(f"[InputManager] Warning: failed to register controller: {exc}", file=sys.stderr)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self._remove_controller(event.instance_id)

    def _remove_controller(self, instance_id):
        self.controllers.pop(instance_id, None)
        for player_idx, assigned_id in self.player_assignments.items():
            if assigned_id == instance_id:
                self.player_assignments[player_idx] = None

    def set_player_keyboard_controls(self, player_index, controls):
        self.player_keyboard_controls[player_index] = controls

    def has_any_controller(self):
        return bool(self.controllers)

    def connected_count(self):
        return len(self.controllers)

    def get_player_device_label(self, player_index):
        assigned = self.player_assignments.get(player_index)
        return "PAD" if assigned in self.controllers else "KB"

    def get_assigned_controller(self, player_index):
        assigned = self.player_assignments.get(player_index)
        return assigned if assigned in self.controllers else None

    def get_controller_name(self, instance_id):
        joystick = self.controllers.get(instance_id)
        if joystick is None:
            return None
        try:
            name = joystick.get_name()
            return name if name else None
        except (pygame.error, AttributeError):
            return None

    def get_controller_display(self, instance_id):
        name = self.get_controller_name(instance_id)
        if name:
            return f"{name} (id {instance_id})"
        return f"Controller #{instance_id}"

    def assign_controller(self, player_index, instance_id):
        if instance_id not in self.controllers:
            return False
        if instance_id in self.player_assignments.values():
            return False
        self.player_assignments[player_index] = instance_id
        return True

    def unassign_player(self, player_index):
        self.player_assignments[player_index] = None

    def auto_assign_for_mode(self, mode):
        self.refresh_controllers()
        available = list(self.controllers.keys())
        if mode == "1p":
            # In 1P mode default to keyboard control for P1 to avoid unwanted
            # analog stick drift when a controller is merely connected.
            self.player_assignments[0] = None
            self.player_assignments[1] = None
        else:
            if len(available) >= 2:
                # Preserve explicit assignments when valid.
                for player_idx in (0, 1):
                    assigned = self.player_assignments[player_idx]
                    if assigned not in self.controllers:
                        self.player_assignments[player_idx] = None
                for player_idx in (0, 1):
                    if self.player_assignments[player_idx] is None:
                        for instance_id in available:
                            if instance_id not in self.player_assignments.values():
                                self.player_assignments[player_idx] = instance_id
                                break
            elif len(available) == 1 and self.player_assignments[0] is None and self.player_assignments[1] is None:
                self.player_assignments[0] = available[0]

    def get_actions(self, player_index, keys):
        actions = {name: False for name in ACTION_NAMES}

        controller_actions = self._read_controller_actions(player_index)
        for name in ACTION_NAMES:
            actions[name] = controller_actions[name]
        return actions

    def _read_controller_actions(self, player_index):
        actions = {name: False for name in ACTION_NAMES}
        instance_id = self.player_assignments.get(player_index)
        if instance_id not in self.controllers:
            return actions
        joystick = self.controllers[instance_id]
        try:
            x_axis = joystick.get_axis(0) if joystick.get_numaxes() > 0 else 0.0
            y_axis = joystick.get_axis(1) if joystick.get_numaxes() > 1 else 0.0
            if abs(x_axis) >= self.dead_zone:
                if x_axis < 0:
                    actions["left"] = True
                else:
                    actions["right"] = True
            if abs(y_axis) >= self.dead_zone:
                if y_axis < 0:
                    actions["up"] = True
                else:
                    actions["down"] = True

            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)
                actions["left"] = actions["left"] or hat_x < 0
                actions["right"] = actions["right"] or hat_x > 0
                actions["up"] = actions["up"] or hat_y > 0
                actions["down"] = actions["down"] or hat_y < 0

            button_count = joystick.get_numbuttons()
            if button_count > 0 and joystick.get_button(0):
                actions["cast"] = True
            if button_count > 5 and joystick.get_button(5):
                actions["spell_next"] = True
            if button_count > 4 and joystick.get_button(4):
                actions["spell_prev"] = True
        except (pygame.error, IndexError) as exc:
            print(f"[InputManager] Warning: controller read error: {exc}", file=sys.stderr)
            return {name: False for name in ACTION_NAMES}

        # Shoulder buttons should trigger once per press, matching keydown behavior.
        prev = self._prev_controller_actions[player_index]
        actions["spell_next"] = actions["spell_next"] and not prev["spell_next"]
        actions["spell_prev"] = actions["spell_prev"] and not prev["spell_prev"]
        prev["spell_next"] = self._button_pressed(instance_id, 5)
        prev["spell_prev"] = self._button_pressed(instance_id, 4)
        return actions

    def _button_pressed(self, instance_id, button_index):
        joystick = self.controllers.get(instance_id)
        if joystick is None:
            return False
        try:
            return joystick.get_numbuttons() > button_index and bool(joystick.get_button(button_index))
        except (pygame.error, IndexError):
            return False

    def get_menu_actions(self):
        merged = {"up": False, "down": False, "confirm": False}
        for joystick in self.controllers.values():
            try:
                axis_y = joystick.get_axis(1) if joystick.get_numaxes() > 1 else 0.0
                hat_y = joystick.get_hat(0)[1] if joystick.get_numhats() > 0 else 0
                confirm = joystick.get_numbuttons() > 0 and joystick.get_button(0)
                merged["up"] = merged["up"] or axis_y <= -self.dead_zone or hat_y > 0
                merged["down"] = merged["down"] or axis_y >= self.dead_zone or hat_y < 0
                merged["confirm"] = merged["confirm"] or bool(confirm)
            except (pygame.error, IndexError) as exc:
                print(f"[InputManager] Warning: menu controller read error: {exc}", file=sys.stderr)

        edge = {
            "up": merged["up"] and not self._menu_prev["up"],
            "down": merged["down"] and not self._menu_prev["down"],
            "confirm": merged["confirm"] and not self._menu_prev["confirm"],
        }
        self._menu_prev = merged
        return edge
