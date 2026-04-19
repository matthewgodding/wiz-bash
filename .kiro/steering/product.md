# Wiz Bash — Product Overview

Wiz Bash is a local 2D wizard battle game built with Python and pygame. Two wizards fight in an arena using a variety of offensive and defensive spells.

## Game Modes
- **1 Player** — human vs. AI opponent at Easy, Medium, or Hard difficulty
- **2 Players** — local co-op on the same keyboard

## Core Gameplay Loop
1. Mode select screen → (1P) difficulty select screen → match
2. Players move around the arena, cycle through spells, and cast at each other
3. First wizard to reduce the opponent's HP to 0 wins
4. Press `R` to return to mode select or `Q` to quit after a match

## Spell System
- 5 offensive spells (projectiles): Fireball, Frost Bolt, Lightning, Arcane Missile, Mana Drain
- 4 defensive spells (instant): Shield, Blink, Counterspell, Heal
- Mana regenerates over time; all spells have individual cooldowns

## AI Difficulty Levels
| Level  | Reaction Delay | Cast Accuracy | Notes                          |
|--------|---------------|---------------|--------------------------------|
| Easy   | 800 ms        | 60%           | Random spell selection, ignores threats 40% of the time |
| Medium | 400 ms        | 85%           | Smart spell selection          |
| Hard   | 100 ms        | 100%          | Optimal, always reacts         |
