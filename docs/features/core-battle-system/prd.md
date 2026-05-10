---
Status: Draft
Owner: Varun
Last updated: 2026-05-08
---

# PRD — Core Battle System

## 1. Problem statement

We need a turn-based battle simulation that faithfully captures the strategic depth of Miscrits. This is the foundation everything else builds on — progression, PvP, and RL agent training all depend on battles working correctly.

Without a correct and extensible battle simulation, none of the downstream goals (tactical depth, RL strategy discovery) are achievable.

## 2. Goals

| Goal | Metric |
|---|---|
| Faithfully replicate Miscrits damage mechanics | Damage output matches expected values for known stat/nature/attack combinations |
| Support all six natures and both elemental triangles | Nature matchup multipliers (2x, 0.5x, 1x) apply correctly in all combinations |
| Support physical and elemental attacks | PA/PD path and EA/ED path produce correct, distinct results |
| Support status effects (DOT, buffs, debuffs, fixed-damage effects) | Effects trigger at correct lifecycle points and resolve correctly |
| Enable programmatic play (no UI dependency) | Battles can be run headlessly via an ActionProvider interface |
| Be extensible without engine changes | New attacks and effects can be added by registration, not by modifying the battle loop |

## 3. Non-goals (v1)

- **Switching miscrits mid-battle** — deferred to v2. v1 battles are 1v1 (one miscrit per side).
- **Leveling and stat growth** — v1 sets instance stats directly.
- **Enchantments** — deferred to v2.
- **Capture mechanic** — deferred to v3.
- **Grade-based stat growth** — deferred to v2. v1 instances have a grade field but it does not affect stats.
- **Evolution** — deferred to v2.
- **UI / multiplayer networking** — deferred indefinitely.
- **RL agent training harness** — deferred to v4. But v1's ActionProvider interface is designed to be RL-compatible.

## 4. User stories

### 4.1 Game designer

> As a game designer, I want to define a new miscrit species by specifying its name, nature(s), base stats, and movelist — and have it immediately usable in battles without changing any engine code.

> As a game designer, I want to define a new attack by specifying its type, power, accuracy, nature, and optional effects — and register it into the catalog.

> As a game designer, I want to add a new status effect (e.g., a new DOT variant) by implementing a well-defined interface and registering it — without touching the battle loop.

### 4.2 Simulation runner

> As a simulation runner, I want to set up a battle between two miscrits with known stats and attacks, run it to completion, and inspect the full turn log — so I can verify mechanics.

> As a simulation runner, I want to plug in different damage formulas or turn-order rules without rewriting the battle engine — so I can experiment with balance.

### 4.3 Future RL agent (design-forward)

> As an RL agent, I want to receive a structured observation of the battle state each turn (my stats, opponent's visible stats, active effects, available moves) and submit an action (attack choice) — so I can learn to play.

This story is not implemented in v1 but the ActionProvider interface must support it without breaking changes.

## 5. Feature specification

### 5.1 Natures and elemental matchups

Six natures, two triangles:

```
Triangle 1: Nature > Water > Fire > Nature
Triangle 2: Wind > Earth > Lightning > Wind
```

**Matchup rules:**
- Attacker's elemental attack nature is **strong** against defender's nature: **2x** damage multiplier.
- Attacker's elemental attack nature is **weak** against defender's nature: **0.5x** damage multiplier.
- Cross-triangle or same-nature: **1x** (neutral).
- Physical attacks are **untyped** — always 1x regardless of natures.

**Dual-natured miscrits:**
- Have one nature from each triangle (e.g., Fire + Wind).
- Their elemental attacks carry **one** of their natures (determined per attack).
- They are **weak to two natures** (one per triangle) and **strong against two natures** (one per triangle).
- When defending, the incoming attack's nature only interacts with the defender's nature in the **same triangle**. The other nature is cross-triangle and always neutral. A "strong against one, weak against the other" scenario is impossible because the two triangles are independent.

### 5.2 Stats

Six stats as defined in vision.md: HP, SPD, PA, EA, PD, ED.

In v1, stats are set directly on the instance. No growth formula, no grade scaling.

### 5.3 Attacks

Each attack has:

| Field | Type | Description |
|---|---|---|
| id | string | Unique identifier |
| name | string | Display name |
| description | string | Flavor text |
| type | PHYSICAL or ELEMENTAL | Determines which attack/defense stats are used |
| nature | Nature (nullable) | For elemental attacks: the nature of the attack. Null for physical. |
| power | int | Base damage (AP term in formula) |
| accuracy | int (0-100) | Chance of hitting |
| effect_ids | list of string | Effects applied on hit |
| target_rule | SELF, SINGLE_OPPONENT | Who the attack targets (ALL_OPPONENTS deferred to multi-miscrit battles) |

### 5.4 Damage calculation

For a physical attack:

```
raw_damage = f(attacker.PA, defender.PD, attack.power)
multiplier = 1.0  (physical is untyped)
final_damage = raw_damage * multiplier
```

For an elemental attack:

```
raw_damage = f(attacker.EA, defender.ED, attack.power)
multiplier = nature_matchup(attack.nature, defender.nature)
final_damage = raw_damage * multiplier
```

The exact formula `f(attack_stat, defense_stat, power)` is encapsulated behind a DamageCalculator interface. The default implementation is TBD (needs reverse-engineering or approximation from the original game). The important contract is:

- Higher attack stat = more damage.
- Higher defense stat = less damage.
- Higher power = more damage.
- The formula is a pure function with no side effects.

### 5.5 Turn order

Each round, the miscrit with higher SPD acts first. Tie-breaking rule is TBD.

In v1 (1v1, no switching), turn order is straightforward. The strategic depth of speed control emerges in v2 when switching is introduced.

### 5.6 Accuracy check

Each attack has an accuracy (0-100). Before damage is calculated, an accuracy roll determines if the attack hits. On miss, no damage is dealt and no effects are applied.

### 5.7 Effects

Effects are the primary extension mechanism. They cover everything that isn't raw damage.

**Effect lifecycle:**

| Trigger | When it fires |
|---|---|
| ON_APPLY | Immediately when the effect is attached to a target |
| ON_TURN_START | At the start of the affected miscrit's turn |
| ON_TURN_END | At the end of the affected miscrit's turn |
| ON_HIT | When the affected miscrit is hit by an attack |
| ON_EXPIRE | When the effect's duration reaches zero and it is removed |

**v1 effect catalog:**

| Effect | Category | Behavior |
|---|---|---|
| Stat buff | Buff | Increases one stat by a fixed amount on apply, reverts on expire |
| Stat debuff | Debuff | Decreases one stat by a fixed amount on apply, reverts on expire |
| DOT (e.g., Burn) | Damage over time | Deals stat-based damage at turn end. Scales with attacker EA / defender ED (hypothesis). |
| HOT (e.g., Regenerate) | Heal over time | Heals a stat-based amount at turn end |
| Poison / Venom | Fixed DOT | Deals fixed damage at turn end. Not affected by stats. Same-type does not stack — reapplication refreshes duration. |
| Switch Curse | Escalating fixed DOT | Deals fixed damage at turn end. Damage increases each turn the target remains active. Does not stack — reapplication refreshes. |
| Negate | Defensive | Removes the target's elemental weakness for the remainder of the battle (until switched out, which is v2). On apply only. |
| Healing | Instant | Restores HP immediately. Targets self. |

**Stacking rules (v1):**
- Stat buffs/debuffs: same-stat buffs/debuffs do not stack. Reapplication refreshes duration and overwrites magnitude. Stacking caps are TBD for v2.
- Fixed DOTs (Poison, Venom, Switch Curse): same-type does not stack; reapplication refreshes duration.
- Stat-based DOT/HOT: TBD whether they stack.

### 5.8 Battle structure (v1)

v1 models **1v1 battles** — one miscrit per side, no switching.

```
Battle setup:
  - Two sides, each with one MiscritInstance
  - Both start at full HP

Round loop:
  1. Determine turn order (SPD comparison)
  2. For each actor in order:
     a. Fire ON_TURN_START for all effects on this actor
     b. Request action from the actor's ActionProvider
     c. If action is an attack:
        - Accuracy check
        - If hit: calculate damage, apply damage, fire ON_HIT, apply attack effects
        - If miss: log miss
     d. Fire ON_TURN_END for all effects on this actor
     e. Tick effect durations, fire ON_EXPIRE for any that reach 0
     f. Check if opponent is fainted (HP <= 0)
  3. If neither side fainted, next round

Win condition: opponent's miscrit reaches 0 HP.
```

### 5.9 ActionProvider interface

The contract between the battle engine and whatever decides moves.

```
interface ActionProvider:
    choose_action(battle_state: BattleObservation) -> Action
```

`BattleObservation` contains:
- Own miscrit: current HP, stats (after buff/debuff modifications), active effects, available attacks.
- Opponent miscrit: current HP, nature(s), active effects visible to the player. (Whether opponent stats are visible is TBD — in the original game some information is hidden.)

`Action` in v1 is simply an attack choice (attack_id). In v2 it expands to include switch.

Implementations:
- **RandomActionProvider** — picks a random valid attack. Used for testing.
- **ScriptedActionProvider** — follows a predefined move sequence. Used for deterministic tests.
- Future: **RLActionProvider** (v4), **HumanInputProvider** (if UI is ever built).

### 5.10 Battle log

Every battle produces a structured turn log capturing:
- Each round's turn order
- Each action taken (attack chosen, target)
- Accuracy roll result (hit/miss)
- Damage dealt (raw, multiplier, final)
- Effects applied, triggered, expired
- HP changes
- Battle outcome

The log is a data structure, not a string. Consumers (test harnesses, RL reward functions, future UI) read it programmatically.

## 6. Data model summary

| Entity | Key fields | Notes |
|---|---|---|
| Miscrit (template) | id, name, nature(s), base_stats (Stat -> int), rarity, movelist (attack_ids) | One per species. Immutable during a battle. |
| MiscritInstance | id, template_id, level, grade, resolved_stats (Stat -> int), current_hp, active_effects | One per owned creature. Stats set directly in v1. |
| Attack | id, name, type, nature, power, accuracy, effect_ids, target_rule | Registered in AttackRegistry. Pure data. |
| Effect | id, duration, triggers, lifecycle hooks | Registered as factories in EffectRegistry. |
| Battle | sides (2x MiscritInstance), turn_history, round_number, status | Runtime container. |

## 7. Testing strategy

| What | How | Why |
|---|---|---|
| Nature matchup table | Unit test all 36 matchups (6x6) | Catch any misclassified matchup |
| Damage calculation | Unit test with known inputs/outputs for both physical and elemental | Verify formula correctness |
| Accuracy check | Statistical test — run 10k rolls at accuracy=75, verify ~75% hit rate | Verify randomness is calibrated |
| Effect lifecycle | Unit test each v1 effect: apply, tick, expire, verify stat/HP changes | Each effect is a distinct behavior |
| Stacking rules | Unit test: apply same buff twice, verify overwrite not stack | Catch stacking bugs early |
| Full battle | Integration test with ScriptedActionProviders, verify turn log matches expected sequence | End-to-end correctness |
| Nature multiplier in battle | Integration test: fire attack vs water defender, verify 2x damage | Nature system works end-to-end |

## 8. Open questions

1. **Exact damage formula** — `f(attack_stat, defense_stat, power)`. Needs reverse-engineering or a design decision.
2. **Speed tie-breaking** — what determines order when SPD is equal?
3. **Opponent information visibility** — in the original game, which opponent stats/effects are visible? This affects the observation space for RL.
4. **Stat-based DOT/HOT stacking** — do they stack, refresh, or overwrite?
5. **Buff/debuff magnitude caps** — is there a maximum number of stages a stat can be buffed/debuffed?
6. **Community term** for fully bonus-trained miscrit.

## 9. Dependencies

- None. This is the foundational feature.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Damage formula doesn't match original game feel | Medium | Medium | Expose formula as a swappable strategy; iterate based on playtesting |
| Effect system too rigid for exotic effects (v2+) | Low | High | Effect interface has 5 lifecycle hooks and access to full battle context — should be sufficient. Monitor as effects are added. |
| 1v1 scope too narrow to validate team-based mechanics | Medium | Low | Acceptable — v1 validates core math and effect lifecycle. Team mechanics are v2. |
