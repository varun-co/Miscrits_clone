---
Status: Draft
Owner: Varun
Last updated: 2026-05-08
References: docs/features/core-battle-system/tdd.md
---

# Feature 1: Enumerations, Value Types, and Project Structure

## 1. Problem statement

Every component in the system depends on shared types (Nature, Stat, Grade, AttackType, etc.) and a consistent project layout. Nothing can be built until these foundations exist. Developers need to know where files go, how modules are organized, and what the shared vocabulary of types looks like.

## 2. Project structure

```
miscrits_clone/
├── docs/                          # Specs, PRDs, TDDs (already exists)
├── src/
│   └── miscrits_clone/
│       ├── __init__.py
│       ├── models/                # Domain entities and value types
│       │   ├── __init__.py
│       │   ├── enums.py           # All enumerations
│       │   ├── value_types.py     # DamageResult, Slot, Action, TurnEntry, etc.
│       │   ├── miscrit.py         # Miscrit template, MiscritInstance
│       │   ├── attack.py          # Attack data model
│       │   ├── effect.py          # Effect interface (ABC)
│       │   ├── player.py          # Player entity
│       │   └── battle.py          # Battle, BattleSide, BattleObservation
│       ├── registries/            # Global catalogs
│       │   ├── __init__.py
│       │   ├── miscrit_registry.py
│       │   ├── attack_registry.py
│       │   └── effect_registry.py
│       ├── engine/                # Combat subsystem
│       │   ├── __init__.py
│       │   ├── battle_engine.py   # Orchestrator
│       │   ├── nature_resolver.py # Elemental matchup logic
│       │   ├── damage_calculator.py
│       │   ├── turn_order.py
│       │   ├── accuracy_checker.py
│       │   └── rng.py             # Seeded RNG wrapper
│       ├── effects/               # v1 effect implementations
│       │   ├── __init__.py
│       │   ├── stat_buff.py
│       │   ├── stat_debuff.py
│       │   ├── burn.py
│       │   ├── regenerate.py
│       │   ├── poison.py
│       │   ├── switch_curse.py
│       │   ├── negate.py
│       │   └── instant_heal.py
│       ├── providers/             # ActionProvider implementations
│       │   ├── __init__.py
│       │   ├── action_provider.py # ABC
│       │   ├── random_provider.py
│       │   └── scripted_provider.py
│       ├── services/              # Player, slots, game state
│       │   ├── __init__.py
│       │   ├── player_service.py
│       │   └── slot_manager.py
│       ├── storage/               # Persistence layer
│       │   ├── __init__.py
│       │   ├── storage_adapter.py # ABC
│       │   ├── file_adapter.py
│       │   └── game_state_store.py
│       └── loader/                # Config-driven startup
│           ├── __init__.py
│           └── data_loader.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_enums.py
│   │   ├── test_value_types.py
│   │   ├── test_nature_resolver.py
│   │   ├── test_miscrit.py
│   │   ├── test_attack.py
│   │   ├── test_registries.py
│   │   ├── test_damage_calculator.py
│   │   ├── test_turn_order.py
│   │   ├── test_accuracy_checker.py
│   │   ├── test_effects.py
│   │   ├── test_action_providers.py
│   │   └── test_miscrit_instance.py
│   └── integration/
│       ├── __init__.py
│       ├── test_battle_engine.py
│       ├── test_storage.py
│       └── test_data_loader.py
├── data/                          # Game content config files
│   ├── miscrits/                  # Species definitions (JSON)
│   └── attacks/                   # Attack definitions (JSON)
├── pyproject.toml
└── README.md
```

**Conventions:**
- Python 3.11+ (for `StrEnum`, improved type hints, `dataclass` features)
- `dataclasses` for value types and entities — frozen where immutable, mutable where needed
- `enum.StrEnum` for enumerations (string-serializable by default)
- `abc.ABC` + `abstractmethod` for interfaces (Effect, ActionProvider, StorageAdapter, strategies)
- `pytest` for testing with `pytest-cov` for coverage
- Type hints everywhere — aim for `mypy --strict` compliance
- No runtime dependencies beyond stdlib for v1 (keep it lean for RL training speed)

## 3. Enumerations (src/miscrits_clone/models/enums.py)

All enums use `StrEnum` for JSON-serializable string values.

| Enum | Members | Notes |
|---|---|---|
| `Nature` | `NATURE, FIRE, WATER, EARTH, LIGHTNING, WIND` | 6 elemental natures |
| `Stat` | `HP, SPD, PD, ED, PA, EA` | 6 stats |
| `Grade` | `F, F_PLUS, E, E_PLUS, D, D_PLUS, C, C_PLUS, B, B_PLUS, A, A_PLUS, S, S_PLUS` | 14 grades, per-instance |
| `StatQuality` | `RED, WHITE, GREEN` | Per-stat growth quality |
| `Rarity` | `COMMON, UNCOMMON, RARE, EPIC, LEGENDARY` | Per-species encounter rate |
| `AttackType` | `PHYSICAL, ELEMENTAL` | Determines stat pair for damage |
| `EffectTrigger` | `ON_APPLY, ON_TURN_START, ON_TURN_END, ON_HIT, ON_EXPIRE` | 5 lifecycle hooks |
| `TargetRule` | `SELF, SINGLE_OPPONENT` | v1 targeting |
| `EffectCategory` | `STAT_BUFF, STAT_DEBUFF, DOT, HOT, FIXED_DOT, HEALING, DEFENSIVE` | Stacking groups |
| `BattleStatus` | `ACTIVE, COMPLETED` | Battle state |
| `StackAction` | `APPLY_NEW, OVERWRITE, REJECT` | Stacking decisions |

**Nature triangle membership helper:**

```
TRIANGLE_1 = {Nature.NATURE, Nature.FIRE, Nature.WATER}
TRIANGLE_2 = {Nature.WIND, Nature.EARTH, Nature.LIGHTNING}

def get_triangle(nature: Nature) -> set[Nature]:
    return TRIANGLE_1 if nature in TRIANGLE_1 else TRIANGLE_2
```

This is a constant + utility, not an enum member — but it belongs in `enums.py` because it's the canonical definition of triangle membership used by validation (Feature 3) and NatureResolver (Feature 2).

## 4. Value types (src/miscrits_clone/models/value_types.py)

All value types are frozen dataclasses unless they need mutability.

**DamageResult** (frozen):

```
@dataclass(frozen=True)
class DamageResult:
    raw_damage: int
    nature_multiplier: float
    final_damage: int
    was_negated: bool
```

**Slot** (frozen):

```
@dataclass(frozen=True)
class Slot:
    index: int
    miscrit_instance_id: str | None = None
```

**Action** (frozen):

```
@dataclass(frozen=True)
class Action:
    attack_id: str
```

**EffectSummary** (frozen):

```
@dataclass(frozen=True)
class EffectSummary:
    effect_id: str
    name: str
    category: EffectCategory
    remaining_duration: int
```

**TurnEntry** (frozen):

```
@dataclass(frozen=True)
class TurnEntry:
    round_number: int
    actor_side: int                        # 0 or 1
    action: Action | None                  # None if fainted before acting
    attack_name: str | None
    hit: bool | None                       # None if no attack (fainted/skipped)
    damage_result: DamageResult | None
    effects_applied: list[str]             # effect IDs attached this turn
    effects_triggered: list[str]           # effect IDs that fired hooks
    effects_expired: list[str]             # effect IDs removed this turn
    hp_after: tuple[int, int]              # (side_0_hp, side_1_hp) after this entry
    fainted: int | None                    # side index that fainted, or None
    battle_ended: bool
```

**ObservedMiscrit** (frozen):

```
@dataclass(frozen=True)
class ObservedMiscrit:
    template_id: str
    natures: list[Nature]
    current_hp: int
    max_hp: int
    resolved_stats: dict[Stat, int]
    base_resolved_stats: dict[Stat, int]
    active_effects: list[EffectSummary]
    available_attacks: list[str]           # attack IDs
```

**OpponentObservation** (frozen):

```
@dataclass(frozen=True)
class OpponentObservation:
    template_id: str
    natures: list[Nature]
    current_hp: int
    max_hp: int
    active_effects: list[EffectSummary]
    stats_visible: bool = False
    resolved_stats: dict[Stat, int] | None = None
```

**BattleObservation** (frozen):

```
@dataclass(frozen=True)
class BattleObservation:
    own_miscrit: ObservedMiscrit
    opponent_miscrit: OpponentObservation
    round_number: int
    turn_log: list[TurnEntry]
```

**BattleResult** (frozen):

```
@dataclass(frozen=True)
class BattleResult:
    winner_side: int | None   # 0, 1, or None for draw
    turn_log: list[TurnEntry]
    total_rounds: int
```

## 5. Testing strategy

| What | How | File |
|---|---|---|
| Enum membership | Verify each enum has expected members and count | `tests/unit/test_enums.py` |
| Nature triangles | `Nature.FIRE` in TRIANGLE_1, `Nature.WIND` in TRIANGLE_2, no overlap | `tests/unit/test_enums.py` |
| `get_triangle` helper | Returns correct set for all 6 natures | `tests/unit/test_enums.py` |
| StrEnum serialization | `str(Nature.FIRE) == "FIRE"`, `Nature("FIRE") == Nature.FIRE` | `tests/unit/test_enums.py` |
| Grade ordering | `Grade.F < Grade.S_PLUS` (if ordering is needed — verify enum order matches intended hierarchy) | `tests/unit/test_enums.py` |
| DamageResult construction | Frozen, all fields accessible | `tests/unit/test_value_types.py` |
| DamageResult immutability | Assignment raises `FrozenInstanceError` | `tests/unit/test_value_types.py` |
| TurnEntry construction | All fields set correctly, frozen | `tests/unit/test_value_types.py` |
| BattleObservation construction | Nested objects (ObservedMiscrit, OpponentObservation) accessible | `tests/unit/test_value_types.py` |
| Slot with and without instance | `Slot(0)` and `Slot(0, "abc")` both valid | `tests/unit/test_value_types.py` |

## 6. Outcome

After this feature is complete:
- The project structure exists and every contributor knows where files go
- All shared types are importable from `miscrits_clone.models.enums` and `miscrits_clone.models.value_types`
- `pytest` runs and passes
- `mypy` passes on all new files
- Every downstream feature (2-12) can import these types without circular dependencies
