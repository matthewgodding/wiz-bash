# Project Structure

## Root Layout
```
wiz-bash/
├── main.py              # Entry point: game loop, HUD rendering, draw_winner, run_game, make_players
├── player.py            # Player class: movement, spell casting, status effects, drawing
├── spells.py            # SPELL_DEFS list, Projectile class, spell constants
├── arena.py             # Arena class: background/border rendering only
├── ai_controller.py     # AIController class + DifficultyConfig dataclass + helper functions
├── menu.py              # show_mode_select(), show_difficulty_select() screen loops
├── requirements.txt
└── tests/
    ├── test_movement_properties.py    # Properties 1–4: AI movement behaviour
    ├── test_spell_properties.py       # Properties 5–8: offensive spell selection
    ├── test_defensive_properties.py   # Properties 9–11: defensive spell logic
    ├── test_difficulty_properties.py  # Properties 12–13: difficulty scaling
    ├── test_menu.py                   # Menu screen return values
    └── test_hud.py                    # HUD and victory message rendering
```

## Module Responsibilities

| Module | Owns |
|--------|------|
| `spells.py` | `SPELL_DEFS` (single source of truth for all spell data), `Projectile`, spell constants (`COUNTER_RADIUS`, `HEAL_AMOUNT`, `SHIELD_HITS`) |
| `player.py` | `Player` class — input handling, casting, status effect timers, pixel-art drawing |
| `ai_controller.py` | `AIController`, `DifficultyConfig`, `EASY`/`MEDIUM`/`HARD` constants, `_lead_target()`, `_is_threat()` helpers |
| `arena.py` | `Arena` class — only draws the floor and border |
| `menu.py` | Blocking event-loop screens that return a mode string or `DifficultyConfig` |
| `main.py` | Wires everything together: `run_game()`, `draw_hud()`, `draw_spell_panel()`, `draw_winner()` |

## Key Conventions

- **Spell indices are positional**: offensive spells are indices 0–4, defensive are 5–8 in `SPELL_DEFS`. Tests and AI logic rely on this ordering — do not reorder entries.
- **`now` is always `pygame.time.get_ticks()` in ms** — passed down from the game loop; never call it inside lower-level classes.
- **`dt` is frame delta in ms** — from `clock.tick(FPS)`; used for timer countdowns and mana regen.
- **Positions are floats** (`self.x`, `self.y`); cast to `int` only at draw time.
- **No pygame in tests** — mock classes (`MockPlayer`, `MockProjectile`, `MockRect`) replicate only the attributes needed; `pygame.Rect` is replaced by `MockRect`.
- **`_apply_instant` lives on `Player`** — the AI calls it directly (`ai._apply_instant(...)`) to trigger defensive spells without going through the keyboard input path.
- **Screen dimensions**: `SCREEN_W=960`, `SCREEN_H=620`; side panels are `PANEL_W=150` each; arena has `left_margin=PANEL_W+10`, `right_margin=PANEL_W+10`.
