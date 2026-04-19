# Implementation Plan: AI Opponent

## Overview

Implement a computer-controlled wizard opponent for Wiz Bash. The work is split into four phases: the `AIController` core logic, the menu screens, wiring everything into `main.py`, and HUD updates. Each phase builds on the previous one and ends with the feature fully integrated.

## Tasks

- [x] 1. Create `ai_controller.py` with `DifficultyConfig` and skeleton `AIController`
  - Define the `DifficultyConfig` dataclass with fields: `name`, `reaction_delay`, `cast_accuracy`, `ignore_threat_prob`, `random_spell_select`
  - Instantiate the three pre-built configs: `EASY`, `MEDIUM`, `HARD` with the exact values from the design
  - Define the `AIController.__init__` storing `ai_wizard`, `config`, and internal state fields (`_next_move_time`, `_next_cast_time`, `_move_dx`, `_move_dy`, `_prev_human_pos`, `_prev_human_time`)
  - Add a stub `update` method that returns `None`
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Implement threat detection and movement logic
  - [x] 2.1 Implement `_is_threat` as a module-level pure function using the dot-product closest-approach formula from the design
    - _Requirements: 3.2_
  - [x] 2.2 Implement `_choose_movement` returning a `(dx, dy)` unit vector
    - No-threat case: move toward/away from human to maintain 200–350 px engagement band
    - Threat case: move perpendicular to the incoming projectile's velocity
    - Boundary avoidance: add inward component when within 80 px of any arena edge
    - Respect `_next_move_time` gate — return current `(_move_dx, _move_dy)` unchanged if `now < _next_move_time`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.3 Write property test for engagement distance maintenance (Property 1)
    - **Property 1: Engagement distance maintenance**
    - **Validates: Requirements 3.1**

  - [x] 2.4 Write property test for perpendicular evasion direction (Property 2)
    - **Property 2: Perpendicular evasion direction**
    - **Validates: Requirements 3.2**

  - [x] 2.5 Write property test for boundary avoidance (Property 3)
    - **Property 3: Boundary avoidance**
    - **Validates: Requirements 3.3**

  - [x] 2.6 Write property test for reaction delay gating movement (Property 4)
    - **Property 4: Reaction delay gates movement updates**
    - **Validates: Requirements 3.4**

- [x] 3. Implement offensive spell selection and lead-aim
  - [x] 3.1 Implement `_lead_target` as a pure function using the constant-velocity approximation from the design; return human's current centre when `spell_speed <= 0` or `dt == 0`
    - _Requirements: 4.4_
  - [x] 3.2 Implement `_choose_spell` returning an offensive spell index or `None`
    - Return `None` when mana < 20
    - On Easy: pick uniformly at random from available (not-on-cooldown, affordable) offensive spells
    - On Medium/Hard: prefer highest-damage spell when human HP > 50%; prefer fastest-projectile spell when human is moving quickly; fall back to next available spell when preferred is on cooldown
    - Respect `cast_accuracy` — skip casting with probability `1 - cast_accuracy`
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [x] 3.3 Write property test for offensive spell always available and within mana (Property 5)
    - **Property 5: Offensive spell is always available and within mana**
    - **Validates: Requirements 4.1, 4.3**

  - [x] 3.4 Write property test for spell preference following game state (Property 6)
    - **Property 6: Spell preference follows game state**
    - **Validates: Requirements 4.2**

  - [x] 3.5 Write property test for lead-aim point ahead of human (Property 7)
    - **Property 7: Lead-aim point is ahead of the human**
    - **Validates: Requirements 4.4**

  - [x] 3.6 Write property test for low mana suppressing offensive casting (Property 8)
    - **Property 8: Low mana suppresses offensive casting**
    - **Validates: Requirements 4.5**

- [x] 4. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement defensive spell logic
  - [x] 5.1 Implement `_should_cast_defensive` returning a defensive spell index or `None`
    - Priority order: Counterspell (multiple threats) → Shield (single threat, HP-proportional probability) → Blink (threat, others unavailable) → Heal (HP < 30%, no threat)
    - Suppress all defensive spells when mana < 30, except Heal when HP < 15%
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 Write property test for defensive spell priority ordering (Property 9)
    - **Property 9: Defensive spell priority ordering**
    - **Validates: Requirements 5.1, 5.2, 5.4**

  - [x] 5.3 Write property test for heal at critical HP (Property 10)
    - **Property 10: Heal at critical HP**
    - **Validates: Requirements 5.3**

  - [x] 5.4 Write property test for low mana suppressing defensive casting (Property 11)
    - **Property 11: Low mana suppresses defensive casting (with Heal exception)**
    - **Validates: Requirements 5.5**

- [x] 6. Implement difficulty-scaled behaviour and wire `AIController.update`
  - [x] 6.1 Apply Easy-difficulty stochastic threat-ignore (`ignore_threat_prob = 0.40`) inside `update` before calling `_choose_movement` and `_should_cast_defensive`
    - _Requirements: 6.1_
  - [x] 6.2 Complete `AIController.update`: call `_choose_movement`, apply position delta to `ai_wizard.x`/`ai_wizard.y` (clamped to arena), call `_should_cast_defensive`, call `_choose_spell`, build and return a `Projectile` aimed at the lead-aim point when an offensive spell is chosen
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.4, 6.2, 6.3_

  - [x] 6.3 Write property test for Easy difficulty stochastic threat ignore (Property 12)
    - **Property 12: Easy difficulty ignores threats stochastically**
    - **Validates: Requirements 6.1**

  - [x] 6.4 Write property test for Easy difficulty uniform random spell selection (Property 13)
    - **Property 13: Easy difficulty uses uniform random spell selection**
    - **Validates: Requirements 6.4**

- [x] 7. Create `menu.py` with mode and difficulty select screens
  - Implement `show_mode_select(screen, fonts) -> str` — renders "1 Player" / "2 Players" buttons, runs its own event loop, returns `"1p"` or `"2p"`
  - Implement `show_difficulty_select(screen, fonts) -> DifficultyConfig` — renders "Easy" / "Medium" / "Hard" buttons, returns the matching config constant
  - _Requirements: 1.1, 1.2, 1.3, 2.1_

  - [x] 7.1 Write unit tests for menu screen return values
    - Verify `show_mode_select` returns `"1p"` on "1 Player" selection and `"2p"` on "2 Players"
    - Verify `show_difficulty_select` returns `EASY`, `MEDIUM`, `HARD` configs with correct field values
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3, 2.4_

- [x] 8. Refactor `main.py` to support 1p/2p mode and integrate `AIController`
  - [x] 8.1 Extract the match loop into `run_game(screen, clock, fonts, arena, mode, difficulty)` — when `mode == "1p"` create an `AIController` and call `ai_controller.update(...)` each frame instead of `p2.handle_input` / `p2.try_cast`
    - _Requirements: 1.2, 2.2_
  - [x] 8.2 Update `main()` to call `show_mode_select` → optionally `show_difficulty_select` → `run_game`; after a match ends, return to `show_mode_select` on restart
    - _Requirements: 1.1, 1.3, 1.4_

- [x] 9. Update HUD rendering for 1-player mode
  - In `draw_spell_panel`, accept an optional `label_override` and `subtitle` parameter; when `mode == "1p"` pass `label_override="CPU"` and `subtitle=difficulty.name` for the AI panel
  - Update `draw_hud` to hide P2 control hints when `mode == "1p"`
  - Update `draw_winner` to accept a `mode` parameter and display "You Win!" / "CPU Wins!" instead of player names in 1p mode
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.1 Write unit tests for HUD and victory message rendering
    - Verify AI panel shows "CPU" label and difficulty name in 1p mode
    - Verify victory message is "You Win!" when human wins and "CPU Wins!" when AI wins in 1p mode
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 10. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use [Hypothesis](https://hypothesis.readthedocs.io/) with a minimum of 100 iterations each
- Each property test file should include a comment `# Feature: ai-opponent, Property N: <property_text>` per the design's testing strategy
- `AIController` never modifies `Player` internals — it only sets `ai_wizard.x`/`ai_wizard.y` and calls `try_cast` via the existing public API
