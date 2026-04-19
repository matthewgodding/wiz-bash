# Wiz Bash

A wizard battle game built with Python and pygame. Play solo against a computer-controlled opponent or go head-to-head with a friend in local 2-player mode.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Game Modes

When you launch the game you'll be shown a **Mode Select** screen:

- **1 Player** — face off against an AI opponent. You'll then pick a difficulty:
  - **Easy** — slow reactions, random spell selection, occasionally ignores threats
  - **Medium** — balanced reactions and smart spell choices
  - **Hard** — fast reactions, optimal spell selection, always reacts to threats
- **2 Players** — local co-op on the same keyboard

After a match ends, press `R` to return to the Mode Select screen or `Q` to quit.

## Controls

|             | Player 1          | Player 2 (2P only) |
|-------------|-------------------|--------------------|
| Move        | `W A S D`         | Arrow keys         |
| Cycle spell | `Q` / `E`         | `,` / `.`          |
| Cast        | `Space`           | `Enter`            |
| Restart     | `R` (after game)  |                    |
| Quit        | `Q` (after game)  |                    |

## Spells

### Offensive

| Spell          | Mana | Damage | Effect                          |
|----------------|------|--------|---------------------------------|
| Fireball       | 25   | 30     | Fast, high damage               |
| Frost Bolt     | 20   | 15     | Slows enemy movement for 3s     |
| Lightning      | 30   | 40     | Very fast projectile            |
| Arcane Missile | 10   | 12     | Cheap and spammable             |
| Mana Drain     | 15   | 5      | Steals 20 mana from the enemy   |

### Defensive `[D]`

| Spell        | Mana | Cooldown | Effect                                        |
|--------------|------|----------|-----------------------------------------------|
| Shield       | 20   | 3s       | Absorbs the next incoming projectile          |
| Blink        | 25   | 2.5s     | Teleports away from the opponent              |
| Counterspell | 30   | 2s       | Destroys all enemy projectiles within range   |
| Heal         | 35   | 4s       | Restores 30 HP                                |

Mana regenerates slowly over time. Defensive spells are marked `[D]` in the spell panel.

## Running Tests

```bash
python -m pytest tests/ -v
```

The test suite covers all 13 AI correctness properties (using [Hypothesis](https://hypothesis.readthedocs.io/) property-based testing) plus unit tests for menus and HUD rendering.

## Project Structure

```
wiz-bash/
├── main.py              # game loop, HUD, input handling
├── player.py            # Player class — movement, casting, status effects, drawing
├── spells.py            # spell definitions, Projectile class
├── arena.py             # arena background rendering
├── ai_controller.py     # AIController — decision logic for the CPU opponent
├── menu.py              # mode select and difficulty select screens
├── requirements.txt
└── tests/
    ├── test_movement_properties.py   # Properties 1–4: AI movement
    ├── test_spell_properties.py      # Properties 5–8: offensive spell selection
    ├── test_defensive_properties.py  # Properties 9–11: defensive spell logic
    ├── test_difficulty_properties.py # Properties 12–13: difficulty scaling
    ├── test_menu.py                  # menu screen return values
    └── test_hud.py                   # HUD and victory message rendering
```
