# TODO — Miscrits Clone v1

## Feature 1: Enumerations, Value Types, and Project Structure

- [ ] **T1.0: Scaffold project** — Create `pyproject.toml` with pytest/mypy config, `src/miscrits_clone/` package structure, `tests/` directories, empty `__init__.py` files. Verify `pytest` runs (0 tests) and `mypy` passes on empty package.
- [ ] **T1.1: Implement enumerations** — All 11 enums in `src/miscrits_clone/models/enums.py` using `StrEnum`. Include `TRIANGLE_1`, `TRIANGLE_2` constants and `get_triangle()` helper. Write `tests/unit/test_enums.py` — membership counts, triangle correctness, StrEnum serialization round-trip.
- [ ] **T1.2: Implement value types** — All frozen dataclasses in `src/miscrits_clone/models/value_types.py`: DamageResult, Slot, Action, EffectSummary, TurnEntry, ObservedMiscrit, OpponentObservation, BattleObservation, BattleResult. Write `tests/unit/test_value_types.py` — construction, immutability, nested access.
- [ ] **T1.3: Verify tooling** — `pytest` passes all tests, `mypy --strict` passes on `src/miscrits_clone/models/`, no import errors when importing from `miscrits_clone.models.enums` and `miscrits_clone.models.value_types`.

## Feature 3: Miscrit Template and Attack Data Models

- [ ] **T3.1: Implement Miscrit template dataclass** — Mutable `@dataclass` in `src/miscrits_clone/models/miscrit.py` with fields: `id`, `name`, `natures`, `rarity`, `base_stats`, `movelist`. Add `__post_init__` validation: natures count (1-2), dual-nature triangle constraint (different triangles), auto-sort (T1 first, T2 second), all 6 base_stats present and in range 1-5, non-empty id/name.
- [ ] **T3.2: Implement movelist CRUD** — `add_attack(attack_id) -> None`, `remove_attack(attack_id) -> None`, `replace_attack(old, new) -> None`, `has_attack(attack_id) -> bool`. No duplicates allowed. `replace_attack` preserves index position.
- [ ] **T3.3: Implement Attack frozen dataclass** — `@dataclass(frozen=True, kw_only=True)` in `src/miscrits_clone/models/attack.py` with fields: `id`, `name`, `description`, `type`, `nature`, `power`, `accuracy`, `effect_ids`, `target_rule`. Add `__post_init__` validation: elemental must have nature, physical must not, power > 0, accuracy 0-100, non-empty id/name.
- [ ] **T3.4: Write Miscrit tests** — `tests/unit/test_miscrit.py`: valid single/dual nature, auto-sort, all rejection cases (empty natures, 3 natures, same triangle, missing stats, stats out of range, empty id/name), full movelist CRUD coverage (add, duplicate reject, remove, remove missing, replace, replace order preservation, has_attack).
- [ ] **T3.5: Write Attack tests** — `tests/unit/test_attack.py`: valid physical/elemental, all rejection cases (elemental+null nature, physical+nature, accuracy bounds, power bounds, empty id/name), frozen immutability check, default values for effect_ids and target_rule.

## Feature 4: Registries (Miscrit, Attack, Effect)

- [ ] **T4.1: Implement MiscritRegistry** — `dict[str, Miscrit]` backed. Methods: `register`, `get`, `unregister`, `list_all`, `list_by_nature`, `list_by_rarity`. Duplicate ID rejected on register. `KeyError` on get/unregister unknown ID.
- [ ] **T4.2: Implement AttackRegistry** — `dict[str, Attack]` backed. Takes `MiscritRegistry` in constructor. Methods: `register`, `get`, `unregister` (with referential integrity check against miscrit movelists), `list_all`, `list_by_type`, `list_by_nature`.
- [ ] **T4.3: Implement EffectRegistry** — `dict[str, Callable[[], Effect]]` backed (factories, not singletons). Takes `AttackRegistry` in constructor. Methods: `register`, `create` (calls factory, returns fresh instance), `unregister` (with referential integrity check against attack effect_ids), `list_ids`.
- [ ] **T4.4: Write registry tests** — `tests/unit/test_registries.py`: register/get round-trip, list filters (nature, rarity, type), duplicate ID rejection, unknown ID errors, unregister success, unregister blocked by references (with error message listing referencing entities), EffectRegistry create-twice independence.

## Feature 5: MiscritInstance and Battle Entities

- [ ] **T5.1: Implement MiscritInstance** — `@dataclass` in `src/miscrits_clone/models/miscrit_instance.py`. Fields: `id`, `template_id`, `level`, `grade`, `stat_qualities`, `resolved_stats`, `current_hp` (auto-init from resolved HP), `active_effects`. Validation: non-empty id/template_id, level 1-35, all 6 stats present and > 0, all 6 stat_qualities present. Properties: `max_hp`, `is_fainted`. HP clamping (0 to max).
- [ ] **T5.2: Implement active effects management** — Methods on MiscritInstance: `add_effect`, `remove_effect` (ValueError if missing), `tick_effects` (decrement durations, return and remove expired), `get_effects_by_category`. Effects use duck typing for `duration` and `category` attributes until Feature 6 defines the ABC.
- [ ] **T5.3: Implement BattleSide** — `@dataclass` in `src/miscrits_clone/models/battle.py`. Fields: `player_id` (nullable), `active_miscrit`, `action_provider` (typed as Any until Feature 8).
- [ ] **T5.4: Implement Battle** — `@dataclass` in `src/miscrits_clone/models/battle.py`. Fields: `id`, `sides` (exactly 2), `round_number` (starts 1), `turn_log` (append-only), `status` (ACTIVE/COMPLETED), `winner` (nullable). Methods: `log_turn`, `complete(winner)` with guards, `get_opponent`, `get_side_index`. Validation: non-empty id, exactly 2 sides.
- [ ] **T5.5: Implement observation builder** — `build_observation(battle, requesting_side, attack_registry, miscrit_registry) -> BattleObservation`. Own side gets full visibility (stats, base stats, attacks). Opponent gets limited view (HP, natures, effects; stats hidden by default).
- [ ] **T5.6: Write MiscritInstance tests** — `tests/unit/test_miscrit_instance.py`: HP auto-init, max_hp, is_fainted, HP clamping (floor 0, ceiling max), effect add/remove/tick/expire/filter, all validation rejection cases.
- [ ] **T5.7: Write Battle and observation tests** — `tests/unit/test_battle.py`: creation, log_turn append-only, complete with guards, get_opponent, get_side_index, validation rejections. Observation builder: own-side full visibility, opponent limited visibility, attack resolution from registry.
