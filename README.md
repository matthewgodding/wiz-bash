# Wiz Bash

A local 2-player wizard battle built with Python and pygame. Two wizards face off in an arena, casting spells and managing mana until one falls.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Controls

|             | Player 1          | Player 2          |
|-------------|-------------------|-------------------|
| Move        | `W A S D`         | Arrow keys        |
| Cycle spell | `Q` / `E`         | `,` / `.`         |
| Cast        | `Space`           | `Enter`           |
| Restart     | `R` (after game)  | `R` (after game)  |
| Quit        | `Q` (after game)  | `Q` (after game)  |

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

## Project Structure

```
arena-rpg/
├── main.py          # game loop, HUD, input handling
├── player.py        # Player class — movement, casting, status effects, drawing
├── spells.py        # spell definitions, Projectile class
├── arena.py         # arena background rendering
└── requirements.txt
```
