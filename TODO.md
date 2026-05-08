# TODO — Miscrits Clone v1

## Feature 1: Enumerations, Value Types, and Project Structure

- [ ] **T1.0: Scaffold project** — Create `pyproject.toml` with pytest/mypy config, `src/miscrits_clone/` package structure, `tests/` directories, empty `__init__.py` files. Verify `pytest` runs (0 tests) and `mypy` passes on empty package.
- [ ] **T1.1: Implement enumerations** — All 11 enums in `src/miscrits_clone/models/enums.py` using `StrEnum`. Include `TRIANGLE_1`, `TRIANGLE_2` constants and `get_triangle()` helper. Write `tests/unit/test_enums.py` — membership counts, triangle correctness, StrEnum serialization round-trip.
- [ ] **T1.2: Implement value types** — All frozen dataclasses in `src/miscrits_clone/models/value_types.py`: DamageResult, Slot, Action, EffectSummary, TurnEntry, ObservedMiscrit, OpponentObservation, BattleObservation, BattleResult. Write `tests/unit/test_value_types.py` — construction, immutability, nested access.
- [ ] **T1.3: Verify tooling** — `pytest` passes all tests, `mypy --strict` passes on `src/miscrits_clone/models/`, no import errors when importing from `miscrits_clone.models.enums` and `miscrits_clone.models.value_types`.
