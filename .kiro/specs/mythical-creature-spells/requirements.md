# Requirements Document

## Introduction

This feature adds a new family of wizard spells that conjure classic mythical creatures to fight on behalf of the caster. The spell set includes both temporary summoned allies (persistent AI-driven units with a finite lifetime) and one-shot summon effects (creatures that appear, perform a single combat action, then disappear). The system must integrate with existing spell casting, cooldown, mana, AI opponent behavior, HUD rendering, and match flow in both 1-Player and 2-Player modes without breaking existing spells or controls.

## Glossary

- **Summon_Spell**: A spell that creates a creature-based combat effect rather than a standard projectile or instant buff.
- **Creature_Entity**: A runtime combat unit created by a Summon_Spell that can move, target, and apply effects.
- **One_Shot_Effect**: A summon that appears, executes one predefined action (for example dive, strike, breath), and despawns immediately after resolving.
- **Summon_Slot**: One active creature slot owned by a player; used to enforce per-player summon caps.
- **Lifetime**: Maximum active duration for a temporary Creature_Entity before automatic despawn.
- **Owner**: The player that cast the Summon_Spell and controls team alignment for the summoned creature.
- **Targeting_Rules**: Deterministic rules for selecting valid targets (enemy wizard and/or enemy summons).
- **Friendly_Fire**: Damage interaction where an entity can affect units on the same team.
- **Summon_Catalog**: The configured list of creature summon spells available in the spell roster.

---

## Requirements

### Requirement 1: Summon Spell Types and Catalog

**User Story:** As a player, I want a varied set of creature summon spells with distinct combat roles, so that summoning adds meaningful tactical choices.

#### Acceptance Criteria

1. THE game SHALL define a Summon_Catalog containing at least five mythical creature spells.
2. THE Summon_Catalog SHALL include at least one One_Shot_Effect summon and at least three temporary Creature_Entity summons.
3. EACH creature spell in the Summon_Catalog SHALL define mana cost, cooldown, role description, and summon behavior type (temporary or one-shot).
4. THE initial creature roles SHALL include all of the following archetypes: melee pressure, ranged pressure, defensive protection, and burst/engage.
5. WHEN a summon spell is unavailable due to cooldown or mana, THEN casting SHALL fail using existing spell failure behavior without crashing or blocking other spells.

---

### Requirement 2: Summon Lifecycle and Ownership

**User Story:** As a developer, I want predictable summon spawn and cleanup behavior, so that creature spells are reliable and do not leak state.

#### Acceptance Criteria

1. WHEN a player successfully casts a temporary Summon_Spell, THE game SHALL spawn a Creature_Entity associated with that player's Owner identity.
2. WHEN a temporary Creature_Entity reaches its Lifetime limit, THEN it SHALL despawn automatically within one frame.
3. WHEN a One_Shot_Effect is cast, THEN the summon action SHALL resolve once and the summon SHALL despawn immediately after resolution.
4. WHEN a round ends or match resets, THEN all active summoned entities SHALL be removed before the next round starts.
5. WHEN an Owner is defeated, THEN that Owner's active temporary Creature_Entities SHALL despawn within one frame.
6. THE game SHALL prevent orphaned summoned entities with missing or invalid Owner references from persisting in the update loop.

---

### Requirement 3: Targeting and Combat Interaction

**User Story:** As a player, I want summoned creatures to engage enemies consistently, so that outcomes feel fair and readable.

#### Acceptance Criteria

1. THE game SHALL apply explicit Targeting_Rules per summon type, including whether it can target enemy wizard, enemy summons, or both.
2. THE default targeting priority for temporary offensive summons SHALL be enemy wizard first, then nearest enemy summon if wizard is unavailable.
3. THE default targeting priority for defensive summons SHALL favor threats nearest to the Owner.
4. SUMMONED creatures SHALL respect arena bounds and SHALL not move or attack outside the playable arena.
5. BY default, Friendly_Fire SHALL be disabled for summoned creatures against the Owner and allied summons unless explicitly configured otherwise.
6. WHEN a summoned attack resolves, THEN damage/effect application SHALL use the same health and status pipelines as existing combat effects.
7. WHEN two opposing summoned entities collide or exchange attacks, THEN resolution SHALL be deterministic and repeatable for the same frame state.

---

### Requirement 4: Summon Limits and Anti-Spam Controls

**User Story:** As a player, I want summon mechanics to remain balanced and responsive, so that matches do not become overcrowded or unplayable.

#### Acceptance Criteria

1. THE game SHALL enforce a configurable maximum number of active temporary Creature_Entities per player using Summon_Slots.
2. WHEN a cast would exceed the player's summon cap, THEN the cast SHALL fail gracefully or replace according to configured policy without crashing.
3. EACH summon spell SHALL be bound by cooldown and mana constraints consistent with existing spell systems.
4. THE game SHALL support concurrent summons from both players in 2P mode without cross-owner state corruption.
5. THE summon subsystem SHALL not reduce the game loop below the existing 60 FPS target on hardware that previously sustained 60 FPS under equivalent non-summon conditions.

---

### Requirement 5: Input and Spell System Integration

**User Story:** As a player, I want to cast creature spells through existing controls, so that I do not need to learn a separate input system.

#### Acceptance Criteria

1. SUMMONED creature spells SHALL be selectable through the existing spell cycling actions (`spell_next`, `spell_prev`).
2. SUMMONED creature spells SHALL be cast through the existing cast action (`cast`) for keyboard and controller users.
3. THE summon feature SHALL integrate with the current spell list and selected spell index model without changing existing control bindings.
4. WHEN summon spells are added, THEN all non-summon spells SHALL retain current behavior, timing, and effectiveness.

---

### Requirement 6: Mode Coverage and AI Opponent Behavior

**User Story:** As a player, I want creature summons to work in all play modes, so that the feature feels complete regardless of mode selection.

#### Acceptance Criteria

1. THE summon spell system SHALL be available in both 1P and 2P modes.
2. IN 2P mode, BOTH players SHALL be able to cast summon spells using their configured input devices.
3. IN 1P mode, THE AI opponent SHALL be capable of selecting and casting summon spells from the same Summon_Catalog used by players.
4. AI summon usage SHALL honor cooldown and mana constraints identically to human players.
5. AI summon decision logic SHALL not stall gameplay or block baseline AI movement/defense behavior.

---

### Requirement 7: HUD and Combat Feedback

**User Story:** As a player, I want clear visual feedback for active summons, so that I can understand battlefield state at a glance.

#### Acceptance Criteria

1. WHEN a player has active temporary summons, THE HUD SHALL display the count of active summons for that player.
2. WHEN a summon has finite Lifetime, THE HUD or in-world indicator SHALL communicate remaining duration in a readable form.
3. SUMMONED entities SHALL have visible owner affiliation cues distinguishing Player 1 and Player 2 ownership.
4. WHEN a One_Shot_Effect resolves, THE game SHALL provide a distinct visual impact cue indicating the action completed.
5. HUD updates for summon spawn/despawn events SHALL appear within one frame of state change.

---

### Requirement 8: Robustness and Error Handling

**User Story:** As a player, I want summon features to fail safely under edge cases, so that unstable summon data does not crash matches.

#### Acceptance Criteria

1. IF a summon spell definition is missing required fields, THEN the game SHALL reject that summon at runtime and log a warning without crashing.
2. IF a summon references an invalid creature behavior type, THEN the game SHALL treat the cast as failed and continue normal gameplay.
3. IF a summon update step raises an exception for one entity, THEN the game SHALL catch the exception, log a warning to stderr, and continue updating remaining game systems for that frame.
4. THE summon subsystem SHALL avoid unbounded per-frame allocations that can cause progressive frame-time degradation during extended matches.
5. THE feature SHALL not alter quit, restart, winner detection, or mode-select loop behavior outside summon-specific effects.
