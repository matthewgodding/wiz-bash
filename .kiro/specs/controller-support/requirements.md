# Requirements Document

## Introduction

This feature adds gamepad/controller support to Wiz Bash, allowing players to use physical game controllers (e.g. Xbox, PlayStation, generic USB/Bluetooth gamepads) instead of — or alongside — the keyboard. Both 1-Player and 2-Player modes must benefit: in 1P mode the human player may use a controller; in 2P mode each player may independently use a controller or the keyboard. The feature must integrate cleanly with the existing `Player` input model and the pygame joystick subsystem without breaking any current keyboard behaviour.

## Glossary

- **Controller**: A physical gamepad device recognised by pygame's joystick subsystem (e.g. Xbox controller, PlayStation controller, generic USB/Bluetooth gamepad).
- **Input_Manager**: The new module responsible for detecting connected controllers, mapping controller events to game actions, and providing a unified input interface to `Player` and the game loop.
- **Action**: A named game input (move_up, move_down, move_left, move_right, cast, spell_next, spell_prev) that can be triggered by either a keyboard key or a controller button/axis.
- **Dead_Zone**: A minimum axis displacement threshold below which analogue stick input is ignored to prevent drift.
- **Player**: The existing `Player` class in `player.py`.
- **Game_Loop**: The `run_game()` function in `main.py`.
- **Menu**: The blocking event-loop screens in `menu.py` (`show_mode_select`, `show_difficulty_select`).
- **Axis**: A continuous analogue input on a controller (e.g. left thumbstick X/Y).
- **Button**: A discrete digital input on a controller (e.g. A/Cross, bumpers).

---

## Requirements

### Requirement 1: Controller Detection

**User Story:** As a player, I want the game to automatically detect connected controllers at startup and when I plug one in during play, so that I do not need to restart the game to use my controller.

#### Acceptance Criteria

1. WHEN the game starts, THE Input_Manager SHALL initialise pygame's joystick subsystem and register all currently connected controllers.
2. WHEN a controller is connected while the game is running, THE Input_Manager SHALL detect and register the new controller without requiring a restart.
3. WHEN a controller is disconnected while the game is running, THE Input_Manager SHALL deactivate that controller's slot and fall back to keyboard input for the affected player.
4. THE Input_Manager SHALL support at least two simultaneously connected controllers.
5. IF no controller is connected, THEN THE Input_Manager SHALL allow all players to continue using keyboard input without error.

---

### Requirement 2: Controller-to-Action Mapping

**User Story:** As a player, I want standard controller buttons and sticks to map to game actions intuitively, so that I can play without consulting a manual.

#### Acceptance Criteria

1. THE Input_Manager SHALL map the left analogue stick axes to the move_up, move_down, move_left, and move_right actions for the assigned player.
2. THE Input_Manager SHALL map the D-pad (hat input) to the move_up, move_down, move_left, and move_right actions as an alternative to the analogue stick.
3. THE Input_Manager SHALL map the primary face button (button index 0, e.g. A/Cross) to the cast action.
4. THE Input_Manager SHALL map the right shoulder button (button index 5, e.g. RB/R1) to the spell_next action.
5. THE Input_Manager SHALL map the left shoulder button (button index 4, e.g. LB/L1) to the spell_prev action.
6. THE Input_Manager SHALL apply a Dead_Zone of 0.2 to all analogue stick axes, ignoring input with absolute value below this threshold.
7. WHERE a player is assigned a controller, THE Input_Manager SHALL continue to accept keyboard input for that player simultaneously.

---

### Requirement 3: Player Input Integration

**User Story:** As a developer, I want controller input to feed into the existing Player input model cleanly, so that no existing gameplay logic needs to change.

#### Acceptance Criteria

1. THE Input_Manager SHALL expose a `get_actions(player_index)` method that returns a dictionary of action names to boolean values, compatible with the existing `controls` dictionary structure used by `Player.handle_input` and `Player.try_cast`.
2. WHEN controller movement input is active, THE Player SHALL move at the same speed as when keyboard movement input is active.
3. WHEN both keyboard and controller movement inputs are active simultaneously for the same player, THE Player SHALL combine the inputs additively, clamped to the arena bounds.
4. THE Input_Manager SHALL translate analogue stick displacement magnitude above the Dead_Zone into a boolean active state for directional actions, preserving the existing discrete movement model.

---

### Requirement 4: Player Assignment

**User Story:** As a player, I want to choose which controller controls which wizard, so that two players can each use their own controller in 2P mode.

#### Acceptance Criteria

1. WHEN 2P mode is selected and at least one controller is connected, THE Menu SHALL display a controller assignment screen allowing each player to claim a controller or use the keyboard.
2. WHEN a player presses any button on an unassigned controller on the assignment screen, THE Input_Manager SHALL assign that controller to that player's slot.
3. WHEN 1P mode is selected and at least one controller is connected, THE Input_Manager SHALL assign the first available controller to Player 1 automatically.
4. IF only one controller is connected in 2P mode and no assignment is made, THEN THE Input_Manager SHALL assign that controller to Player 1 and keyboard to Player 2 by default.
5. THE Input_Manager SHALL prevent the same controller from being assigned to both players simultaneously.

---

### Requirement 5: Menu Navigation with Controller

**User Story:** As a player, I want to navigate the mode select and difficulty select menus using my controller, so that I never need to touch the keyboard.

#### Acceptance Criteria

1. WHEN a controller is connected on the mode select screen, THE Menu SHALL accept D-pad up/down or left analogue stick up/down to highlight menu options.
2. WHEN a menu option is highlighted, THE Menu SHALL accept the primary face button (button index 0) to confirm the selection.
3. WHEN the difficulty select screen is shown, THE Menu SHALL accept the same controller navigation inputs as the mode select screen.
4. IF no controller is connected, THEN THE Menu SHALL continue to accept mouse clicks as the sole navigation method without error.

---

### Requirement 6: HUD Controller Indicator

**User Story:** As a player, I want to see which input device I am using in the HUD, so that I can confirm my controller is recognised.

#### Acceptance Criteria

1. WHEN a controller is assigned to a player, THE Game_Loop SHALL display a controller icon or label (e.g. "🎮") next to that player's name in the spell panel.
2. WHEN a player is using keyboard input only, THE Game_Loop SHALL display the existing keyboard hint text unchanged.
3. WHEN a controller is disconnected mid-match, THE Game_Loop SHALL update the HUD to remove the controller indicator for the affected player within one frame.

---

### Requirement 7: Robustness and Error Handling

**User Story:** As a player, I want the game to handle unexpected controller behaviour gracefully, so that a faulty or unsupported controller does not crash the game.

#### Acceptance Criteria

1. IF a controller reports an axis index outside the expected range, THEN THE Input_Manager SHALL ignore that axis event and continue normal operation.
2. IF a controller reports a button index outside the expected range, THEN THE Input_Manager SHALL ignore that button event and continue normal operation.
3. IF pygame raises an exception when reading controller state, THEN THE Input_Manager SHALL catch the exception, log a warning to stderr, and return all actions as inactive for that frame.
4. THE Input_Manager SHALL not introduce any per-frame processing overhead that causes the game loop to drop below 60 FPS on hardware that previously sustained 60 FPS.
