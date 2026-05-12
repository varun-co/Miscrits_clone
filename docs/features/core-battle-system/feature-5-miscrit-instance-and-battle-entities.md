---
Status: Draft
Owner: Varun
Last updated: 2026-05-12
References: docs/features/core-battle-system/tdd.md §2.3, §3.3, §5.1, Issue #5
---

# Feature 5: MiscritInstance and Battle Entities

## 1. Problem statement

Battles need mutable runtime state. Templates (Feature 3) define what a species *is* — base stats, natures, movelist. But a battle operates on *instances*: a specific creature with current HP, active effects, and temporarily modified stats. The engine also needs a container that holds the two sides, tracks rounds, and accumulates a structured log. Without these runtime entities, the BattleEngine has nothing to manipulate.

## 2. Scope and boundaries

**In scope:**
- `MiscritInstance` — the mutable, per-creature battle entity
- `BattleSide` — connects an instance to a decision-maker
- `Battle` — the arena container (sides, rounds, log, status)
- Observation builder — constructs `BattleObservation` with correct visibility per side
- Active effect management on MiscritInstance (add, remove, tick, expire)

**Not in scope:**
- **Effect ABC** — Feature 6 defines the Effect interface. MiscritInstance stores effect instances but doesn't define the interface.
- **ActionProvider interface** — Feature 8. BattleSide holds a reference to one, but the interface is defined elsewhere.
- **BattleEngine** — Feature 9. Battle is the data; the engine is the logic that mutates it.
- **Stat growth / leveling** — v2. In v1, `resolved_stats` and `level` are set directly at construction.
- **Team / switching** — v2. In v1, each BattleSide holds exactly one MiscritInstance.
- **Persistence** — Feature 10. These entities are in-memory runtime objects.

**Lifecycle:**
```
MiscritInstance created with explicit stats
    → assigned to a BattleSide (with an ActionProvider)
    → two BattleSides placed into a Battle
    → BattleEngine mutates the Battle round by round
    → Battle reaches COMPLETED status with a winner
```

## 3. Why three abstractions?

### MiscritInstance: "the creature fighting now"

A Miscrit template says "Fire Sprite has base stats [3,3,2,4,2,3]." A MiscritInstance says "THIS Fire Sprite has 87/120 HP, a burn DOT ticking, and EA temporarily boosted by +10 from a buff." It's the mutable, per-creature state the engine reads and writes every turn.

Key separation from the template:
- Template is shared (one per species, in MiscritRegistry)
- Instance is unique (one per owned creature, carries its own HP/effects/stats)
- Template is read-only during battle; instance is mutated constantly

### BattleSide: "one seat at the table"

A side connects three things:
1. **Who's fighting** — the active MiscritInstance
2. **Who's deciding** — the ActionProvider (random bot, scripted sequence, RL agent)
3. **Who owns it** — the player_id (nullable for AI opponents)

Why not put these on MiscritInstance? Because the creature doesn't know who decides its moves or who owns it. That's context about the *battle participant*, not the *creature*. In v2, BattleSide expands to hold a team of miscrits with one active — the creature model stays unchanged.

### Battle: "the arena"

The single object the BattleEngine operates on. It holds:
- The two sides (always exactly 2 in v1)
- The round counter
- The append-only turn log
- The status (ACTIVE → COMPLETED) and winner

Without Battle, the engine would pass `(side_a, side_b, round_number, log, status, winner)` as loose arguments — fragile and hard to snapshot for observation building.

## 4. Data structures

### 4.1 MiscritInstance

```python
from dataclasses import dataclass, field
from miscrits_clone.models.enums import Grade, Stat, StatQuality

@dataclass
class MiscritInstance:
    id: str
    template_id: str
    level: int
    grade: Grade
    stat_qualities: dict[Stat, StatQuality]
    resolved_stats: dict[Stat, int]
    current_hp: int = field(init=False)
    active_effects: list[Any] = field(default_factory=list)  # list[Effect] after Feature 6

    def __post_init__(self) -> None:
        # current_hp auto-initializes from resolved HP
        self.current_hp = self.resolved_stats[Stat.HP]
        # Validation: non-empty id, level 1-35, all 6 stats present, all 6 stat_qualities present
```

| Field | Type | Mutable? | Description |
|---|---|---|---|
| `id` | str | No | Unique instance identifier |
| `template_id` | str | No | References Miscrit template in MiscritRegistry |
| `level` | int | No | 1-35. Set directly in v1. |
| `grade` | Grade | No | Instance quality. Stored, not used for calculation in v1. |
| `stat_qualities` | dict[Stat, StatQuality] | No | Per-stat RED/WHITE/GREEN. All 6 stats required. |
| `resolved_stats` | dict[Stat, int] | Yes | Actual stat values used in battle. Buffs/debuffs modify these at runtime. |
| `current_hp` | int | Yes | Auto-initialized to `resolved_stats[Stat.HP]`. Decremented by damage, incremented by heals. |
| `active_effects` | list | Yes | Currently attached effects with remaining duration and state. |

**Validation (`__post_init__`):**
- `id` must be non-empty (stripped)
- `template_id` must be non-empty (stripped)
- `level` must be 1-35
- `stat_qualities` must contain all 6 `Stat` keys
- `resolved_stats` must contain all 6 `Stat` keys, all values > 0

**current_hp behavior:**
- Initialized to `resolved_stats[Stat.HP]` automatically (not passed by caller)
- Clamped: cannot go below 0, cannot exceed `resolved_stats[Stat.HP]` (max HP)
- Helper property: `is_fainted -> bool` = `current_hp <= 0`
- Helper property: `max_hp -> int` = `resolved_stats[Stat.HP]`

**Active effects management:**

```python
def add_effect(self, effect: Any) -> None: ...
def remove_effect(self, effect: Any) -> None: ...
def tick_effects(self) -> list[Any]: ...   # decrements durations, returns expired effects
def get_effects_by_category(self, category: EffectCategory) -> list[Any]: ...
```

- `add_effect` — appends to `active_effects`
- `remove_effect` — removes specific effect instance from `active_effects`. Raises `ValueError` if not found.
- `tick_effects` — decrements duration on all effects by 1. Removes and returns any that reach 0 (so the caller can fire `on_expire`). Effects with duration=0 (instant) should never be in `active_effects` — they fire `on_apply` and are never added.
- `get_effects_by_category` — filters active effects by `EffectCategory`. Used by stacking logic.

### 4.2 BattleSide

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class BattleSide:
    player_id: str | None
    active_miscrit: MiscritInstance
    action_provider: Any  # ActionProvider after Feature 8
```

| Field | Type | Description |
|---|---|---|
| `player_id` | str \| None | Null for AI/bot sides |
| `active_miscrit` | MiscritInstance | The one fighting miscrit in v1 |
| `action_provider` | Any | Who decides moves. Typed as `Any` until Feature 8 defines ActionProvider ABC. |

No validation needed — a side is a simple container. In v2, this expands to hold `team: list[MiscritInstance]` with `active_index: int`.

### 4.3 Battle

```python
from dataclasses import dataclass, field
from miscrits_clone.models.enums import BattleStatus
from miscrits_clone.models.value_types import TurnEntry

@dataclass
class Battle:
    id: str
    sides: list[BattleSide]
    round_number: int = 1
    turn_log: list[TurnEntry] = field(default_factory=list)
    status: BattleStatus = BattleStatus.ACTIVE
    winner: BattleSide | None = None

    def __post_init__(self) -> None:
        # Validation: exactly 2 sides, non-empty id
```

| Field | Type | Mutable? | Description |
|---|---|---|---|
| `id` | str | No | Unique battle identifier |
| `sides` | list[BattleSide] | No | Exactly 2 sides. Validated at construction. |
| `round_number` | int | Yes | Starts at 1, incremented by the engine each round |
| `turn_log` | list[TurnEntry] | Append-only | Structured history of every action and outcome |
| `status` | BattleStatus | Yes | ACTIVE → COMPLETED |
| `winner` | BattleSide \| None | Yes | Set when status becomes COMPLETED |

**Validation (`__post_init__`):**
- `id` must be non-empty (stripped)
- `sides` must have exactly 2 elements

**Methods:**

```python
def log_turn(self, entry: TurnEntry) -> None: ...
def complete(self, winner: BattleSide) -> None: ...
def get_opponent(self, side: BattleSide) -> BattleSide: ...
def get_side_index(self, side: BattleSide) -> int: ...
```

- `log_turn` — appends a TurnEntry. Turn log is append-only: no modification or removal of existing entries.
- `complete(winner)` — sets `status = COMPLETED` and `winner = winner`. Raises `ValueError` if already completed. Raises `ValueError` if `winner` is not one of the battle's sides.
- `get_opponent(side)` — returns the other side. Raises `ValueError` if `side` is not in this battle.
- `get_side_index(side)` — returns 0 or 1. Used for TurnEntry.actor_side.

### 4.4 Observation builder

A module-level function (not a class) that constructs `BattleObservation` from a Battle and a requesting side.

```python
def build_observation(
    battle: Battle,
    requesting_side: BattleSide,
    attack_registry: AttackRegistry,
    miscrit_registry: MiscritRegistry,
) -> BattleObservation: ...
```

**Visibility rules:**

| Data | Own side | Opponent side |
|---|---|---|
| template_id | Yes | Yes |
| natures | Yes | Yes |
| current_hp | Yes | Yes |
| max_hp | Yes | Yes |
| resolved_stats (current, after buffs) | Yes | Only if `stats_visible=True` (default False in v1) |
| base_resolved_stats (before buffs) | Yes | No |
| active_effects | Full list | Full list (visible effects = all in v1) |
| available_attacks | Full list (resolved from template movelist via AttackRegistry) | No |

**Why it needs registries:** The observation builder resolves `template_id` → natures (from MiscritRegistry) and movelist attack IDs → Attack objects (from AttackRegistry) to populate `available_attacks` and `natures`.

**Construction logic:**
1. Identify requesting side and opponent side via `battle.get_opponent(requesting_side)`
2. Look up requesting side's miscrit template from MiscritRegistry to get natures and movelist
3. Resolve movelist attack IDs to Attack objects from AttackRegistry
4. Build `ObservedMiscrit` with full visibility
5. Look up opponent's template for natures
6. Build `OpponentObservation` with limited visibility (`stats_visible=False` by default)
7. Return `BattleObservation` with both, plus `round_number` and `turn_log`

## 5. Construction order

```python
# 1. Create instances with explicit stats (v1)
instance_a = MiscritInstance(
    id="inst_001",
    template_id="fire_sprite",
    level=10,
    grade=Grade.B,
    stat_qualities={Stat.HP: StatQuality.GREEN, ...},
    resolved_stats={Stat.HP: 120, Stat.SPD: 45, Stat.PA: 30, Stat.EA: 55, Stat.PD: 25, Stat.ED: 35},
)
# current_hp is automatically 120

# 2. Create sides
side_a = BattleSide(player_id="player_1", active_miscrit=instance_a, action_provider=some_provider)
side_b = BattleSide(player_id=None, active_miscrit=instance_b, action_provider=random_provider)

# 3. Create battle
battle = Battle(id="battle_001", sides=[side_a, side_b])

# 4. Engine runs the battle (Feature 9)
result = engine.run_battle(battle)
```

## 6. Testing strategy

### MiscritInstance (`tests/unit/test_miscrit_instance.py`)

| Test | Setup | Expected |
|---|---|---|
| Create with valid stats | HP=120 in resolved_stats | current_hp = 120 |
| current_hp auto-initializes | Don't pass current_hp | current_hp == resolved_stats[HP] |
| max_hp property | resolved_stats[HP]=120 | max_hp == 120 |
| is_fainted false | current_hp=50 | is_fainted == False |
| is_fainted true | current_hp=0 | is_fainted == True |
| HP clamped at 0 | Set current_hp to -10 | current_hp == 0 |
| HP clamped at max | Set current_hp to max+50 | current_hp == max_hp |
| Add effect | add_effect(fake_effect) | fake_effect in active_effects |
| Remove effect | add then remove | active_effects is empty |
| Remove missing effect | remove non-existent | ValueError |
| Tick effects: decrement | Effect with duration=3, tick once | duration == 2 |
| Tick effects: expire | Effect with duration=1, tick | Returned in expired list, removed from active |
| Tick effects: keep non-expired | Effect with duration=3, tick | Still in active_effects |
| get_effects_by_category | 2 DOTs + 1 BUFF | get_effects_by_category(DOT) returns 2 |
| Invalid: empty id | id="" | ValueError |
| Invalid: level 0 | level=0 | ValueError |
| Invalid: level 36 | level=36 | ValueError |
| Invalid: missing stat | Only 5 resolved_stats | ValueError |
| Invalid: missing stat_quality | Only 5 stat_qualities | ValueError |
| Invalid: stat value <= 0 | HP=0 | ValueError |

### Battle (`tests/unit/test_battle.py`)

| Test | Setup | Expected |
|---|---|---|
| Create valid battle | 2 sides | round_number=1, status=ACTIVE, winner=None |
| log_turn | Append TurnEntry | turn_log has 1 entry |
| log_turn append-only | Append 2 entries | turn_log has 2, order preserved |
| complete(winner) | Set winner to side_a | status=COMPLETED, winner=side_a |
| complete already completed | Call complete twice | ValueError |
| complete invalid winner | Winner not in sides | ValueError |
| get_opponent | Pass side_a | Returns side_b |
| get_opponent invalid | Pass unknown side | ValueError |
| get_side_index | Pass side_a | Returns 0 |
| Invalid: 1 side | Only 1 BattleSide | ValueError |
| Invalid: 3 sides | 3 BattleSides | ValueError |
| Invalid: empty id | id="" | ValueError |

### Observation builder (`tests/unit/test_battle.py`)

| Test | Setup | Expected |
|---|---|---|
| Own side: full visibility | Build observation for side_a | resolved_stats present, base_resolved_stats present, available_attacks populated |
| Opponent: limited visibility | Build observation, check opponent | stats_visible=False, resolved_stats=None, natures/HP visible |
| Available attacks resolved | Template has ["fireball", "tackle"] | available_attacks contains 2 attack IDs |
| Round number and turn log | Battle at round 3 with 4 log entries | observation.round_number=3, len(turn_log)=4 |

## 7. File mapping

| File | Purpose |
|---|---|
| `src/miscrits_clone/models/miscrit_instance.py` | MiscritInstance |
| `src/miscrits_clone/models/battle.py` | Battle, BattleSide, build_observation() |
| `tests/unit/test_miscrit_instance.py` | MiscritInstance tests |
| `tests/unit/test_battle.py` | Battle, BattleSide, observation builder tests |

**Note:** MiscritInstance gets its own file rather than sharing with the Miscrit template. They serve different purposes (static template vs mutable runtime state) and will diverge further in v2 when the instance gains per-instance movesets and growth.

## 8. Open questions

1. **Effect typing** — MiscritInstance stores `list[Any]` until Feature 6 defines the Effect ABC. `tick_effects` needs to read a `duration` attribute on each effect. Should we define a minimal protocol (just `duration: int` and `category: EffectCategory`) now, or use duck typing and fix it when Feature 6 lands?
2. **HP clamping strategy** — should `current_hp` be a property with a setter that clamps, or should callers use `take_damage(amount)` / `heal(amount)` methods that enforce bounds? The method approach is safer (can't accidentally set HP to 999) but the property approach is simpler.

## 9. Outcome

After this feature:
- MiscritInstance exists as a mutable runtime entity with auto-initialized HP and effect management
- BattleSide connects a creature to a decision-maker
- Battle provides the arena container with append-only logging and completion semantics
- The observation builder produces correctly scoped views for each side
- All runtime state needed for the BattleEngine (Feature 9) to operate is in place
