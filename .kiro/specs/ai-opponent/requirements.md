# Requirements Document

## Introduction

This feature adds an AI opponent to Wiz Bash, allowing a single player to compete against a computer-controlled wizard. The AI must feel like a genuine opponent — it navigates the arena, selects spells intelligently based on game state, and uses defensive abilities reactively. The feature also introduces a difficulty selector (Easy / Medium / Hard) so players can tune the challenge. No changes to the existing two-player mode are required.

## Glossary

- **AI_Controller**: The module responsible for all decision-making for the computer-controlled wizard.
- **AI_Wizard**: The `Player` instance controlled by the `AI_Controller` rather than keyboard input.
- **Human_Wizard**: The `Player` instance controlled by the human player via keyboard.
- **Difficulty**: A setting (Easy, Medium, or Hard) that governs how accurately and how quickly the AI reacts.
- **Reaction_Delay**: A configurable per-difficulty timer (in milliseconds) that introduces a lag before the AI acts on new information, simulating human reaction time.
- **Threat**: An enemy projectile whose trajectory will intersect the AI_Wizard's position within a defined time window.
- **Mode_Select_Screen**: The pre-game screen where the player chooses between 1-Player and 2-Player mode.
- **Difficulty_Select_Screen**: The screen shown after choosing 1-Player mode where the player picks a Difficulty level.

---

## Requirements

### Requirement 1: Mode Selection

**User Story:** As a player, I want to choose between playing against another human or an AI opponent, so that I can play solo when no second player is available.

#### Acceptance Criteria

1. WHEN the game is launched, THE Mode_Select_Screen SHALL display options for "1 Player" and "2 Players".
2. WHEN the player selects "2 Players", THE game SHALL start a match with two human-controlled wizards using the existing keyboard controls.
3. WHEN the player selects "1 Player", THE Difficulty_Select_Screen SHALL be displayed before the match begins.
4. WHEN a match ends, THE Mode_Select_Screen SHALL be accessible via the existing restart flow.

---

### Requirement 2: Difficulty Selection

**User Story:** As a player, I want to choose a difficulty level before facing the AI, so that I can find a challenge appropriate to my skill level.

#### Acceptance Criteria

1. WHEN the Difficulty_Select_Screen is shown, THE Difficulty_Select_Screen SHALL present three options: "Easy", "Medium", and "Hard".
2. WHEN the player selects a Difficulty, THE game SHALL start a 1-player match with the AI_Controller configured for that Difficulty.
3. THE AI_Controller SHALL use a Reaction_Delay of 800 ms on Easy, 400 ms on Medium, and 100 ms on Hard.
4. THE AI_Controller SHALL apply a cast accuracy modifier of 60% on Easy, 85% on Medium, and 100% on Hard, reducing the frequency with which the AI chooses to cast.

---

### Requirement 3: AI Movement

**User Story:** As a player, I want the AI wizard to move around the arena purposefully, so that the fight feels dynamic rather than like hitting a stationary target.

#### Acceptance Criteria

1. WHILE no Threat is detected, THE AI_Controller SHALL move the AI_Wizard to maintain a preferred engagement distance of 200–350 pixels from the Human_Wizard.
2. WHEN a Threat is detected, THE AI_Controller SHALL move the AI_Wizard perpendicular to the incoming projectile's trajectory to evade it.
3. WHILE the AI_Wizard is within 80 pixels of an arena boundary, THE AI_Controller SHALL steer the AI_Wizard away from that boundary.
4. THE AI_Controller SHALL update the AI_Wizard's movement direction at most once every Reaction_Delay milliseconds, preventing superhuman instant course corrections.

---

### Requirement 4: Offensive Spell Casting

**User Story:** As a player, I want the AI to cast offensive spells at me, so that I have to actively defend myself during the fight.

#### Acceptance Criteria

1. WHEN the AI_Controller decides to cast and the AI_Wizard has sufficient mana, THE AI_Controller SHALL select an offensive spell from the available spell list.
2. WHEN selecting an offensive spell, THE AI_Controller SHALL prefer higher-damage spells when the Human_Wizard's HP is above 50% and prefer faster-projectile spells when the Human_Wizard is moving quickly.
3. WHEN the selected offensive spell is on cooldown, THE AI_Controller SHALL select the next available offensive spell rather than waiting.
4. THE AI_Controller SHALL lead the Human_Wizard's position when aiming projectile spells, calculating a target point based on the Human_Wizard's current velocity and the spell's projectile speed.
5. IF the AI_Wizard's mana is below 20, THEN THE AI_Controller SHALL not cast any offensive spell.

---

### Requirement 5: Defensive Spell Usage

**User Story:** As a player, I want the AI to use defensive spells reactively, so that the fight requires more than just spamming attacks.

#### Acceptance Criteria

1. WHEN a Threat is detected and the Shield spell is available, THE AI_Controller SHALL cast Shield with a probability proportional to the AI_Wizard's remaining HP (higher probability at lower HP).
2. WHEN multiple Threats are detected simultaneously and Counterspell is available, THE AI_Controller SHALL cast Counterspell to destroy the incoming projectiles.
3. WHEN the AI_Wizard's HP falls below 30% and Heal is available and no Threat is detected, THE AI_Controller SHALL cast Heal.
4. WHEN a Threat is detected and neither Shield nor Counterspell is available, THE AI_Controller SHALL use Blink if it is available.
5. IF the AI_Wizard's mana is below 30, THEN THE AI_Controller SHALL not cast any defensive spell except Heal when HP is below 15%.

---

### Requirement 6: Difficulty-Scaled Behaviour

**User Story:** As a player, I want the AI's skill to match the chosen difficulty, so that Easy feels forgiving and Hard feels like a real challenge.

#### Acceptance Criteria

1. WHILE playing on Easy difficulty, THE AI_Controller SHALL ignore Threats with a 40% probability, simulating missed reactions.
2. WHILE playing on Medium difficulty, THE AI_Controller SHALL react to all Threats but apply the 400 ms Reaction_Delay before changing behaviour.
3. WHILE playing on Hard difficulty, THE AI_Controller SHALL react to all Threats within the 100 ms Reaction_Delay and use optimal spell selection at all times.
4. WHILE playing on Easy difficulty, THE AI_Controller SHALL select spells randomly from the available offensive spells rather than using the preference logic in Requirement 4.

---

### Requirement 7: HUD and Controls Hint Update

**User Story:** As a player, I want the on-screen HUD to reflect that I'm playing against an AI, so that the interface is not confusing.

#### Acceptance Criteria

1. WHEN a 1-player match is active, THE HUD SHALL label the AI_Wizard's panel with "CPU" and display the active Difficulty level beneath the name.
2. WHEN a 1-player match is active, THE HUD SHALL display only the human player's control hints at the bottom of the screen.
3. WHEN a 1-player match is active and the Human_Wizard wins, THE game SHALL display "You Win!" instead of the player name in the victory message.
4. WHEN a 1-player match is active and the AI_Wizard wins, THE game SHALL display "CPU Wins!" in the victory message.
