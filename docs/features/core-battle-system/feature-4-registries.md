---
Status: Draft
Owner: Varun
Last updated: 2026-05-12
References: docs/features/core-battle-system/tdd.md §3.1, §4.1-4.3, Issue #4
---

# Feature 4: Registries (Miscrit, Attack, Effect)

## 1. Problem statement

The system needs global catalogs to look up species, attacks, and effects by ID. The BattleEngine resolves attack IDs from movelists, the effect system creates effect instances by ID, and nothing can reference anything without these lookups. Registries are the mechanism that enables "add content without changing engine code."

## 2. Scope and boundaries

**In scope:**
- Three in-memory registry classes with register/get/list/unregister
- Referential integrity on unregister (reject if still referenced)
- Filter support on list operations

**Not in scope:**
- **Persistence** — registries are not saved to disk. They hold static game content (templates, attack definitions), not mutable state. They are rebuilt from config files every process start.
- **Population** — who calls `register()` is Feature 12 (DataLoader). This feature only builds the container.
- **Effect ABC** — the Effect interface is Feature 6. EffectRegistry stores factories that produce Effect instances, but the Effect type itself is defined elsewhere.

**Lifecycle:**
```
Process start → DataLoader reads JSON configs → calls register() on each registry → Registries are read-only for the rest of the process
```

Registries are **not** thread-safe in v1 (single-threaded battle sim). If v4 RL training parallelizes battles, registries are read-only at that point so no locking needed.

## 3. Underlying data structures

All three registries are thin wrappers around a `dict[str, T]` keyed by entity ID.

### 3.1 MiscritRegistry

```python
from miscrits_clone.models.enums import Nature, Rarity
from miscrits_clone.models.miscrit import Miscrit

class MiscritRegistry:
    _store: dict[str, Miscrit]

    def __init__(self) -> None: ...

    def register(self, miscrit: Miscrit) -> None: ...
    def get(self, id: str) -> Miscrit: ...
    def unregister(self, id: str) -> None: ...
    def list_all(self) -> list[Miscrit]: ...
    def list_by_nature(self, nature: Nature) -> list[Miscrit]: ...
    def list_by_rarity(self, rarity: Rarity) -> list[Miscrit]: ...
```

| Method | Behavior |
|---|---|
| `register(miscrit)` | Adds to `_store` keyed by `miscrit.id`. Raises `ValueError` if ID already registered. |
| `get(id)` | Returns `_store[id]`. Raises `KeyError` with message `"Miscrit '{id}' not found in registry"` if missing. |
| `unregister(id)` | Removes from `_store`. Raises `KeyError` if not found. No referential integrity checks needed (miscrits are leaf entities in v1). |
| `list_all()` | Returns `list(_store.values())`. |
| `list_by_nature(nature)` | Returns all miscrits where `nature in miscrit.natures`. |
| `list_by_rarity(rarity)` | Returns all miscrits where `miscrit.rarity == rarity`. |

### 3.2 AttackRegistry

```python
from miscrits_clone.models.enums import AttackType, Nature
from miscrits_clone.models.attack import Attack

class AttackRegistry:
    _store: dict[str, Attack]
    _miscrit_registry: MiscritRegistry

    def __init__(self, miscrit_registry: MiscritRegistry) -> None: ...

    def register(self, attack: Attack) -> None: ...
    def get(self, id: str) -> Attack: ...
    def unregister(self, id: str) -> None: ...
    def list_all(self) -> list[Attack]: ...
    def list_by_type(self, attack_type: AttackType) -> list[Attack]: ...
    def list_by_nature(self, nature: Nature) -> list[Attack]: ...
```

| Method | Behavior |
|---|---|
| `register(attack)` | Adds to `_store` keyed by `attack.id`. Raises `ValueError` if ID already registered. |
| `get(id)` | Returns `_store[id]`. Raises `KeyError` with message `"Attack '{id}' not found in registry"` if missing. |
| `unregister(id)` | Checks all miscrits in `_miscrit_registry` for references in their movelists. If any reference this ID, raises `ValueError` listing the referencing miscrit IDs. Otherwise removes from `_store`. Raises `KeyError` if ID not found. |
| `list_all()` | Returns `list(_store.values())`. |
| `list_by_type(attack_type)` | Returns all attacks where `attack.type == attack_type`. |
| `list_by_nature(nature)` | Returns all attacks where `attack.nature == nature`. |

**Why AttackRegistry takes MiscritRegistry:** unregister needs to scan miscrit movelists for references. This is the only cross-registry dependency. It's injected at construction, not imported globally.

### 3.3 EffectRegistry

```python
from typing import Callable, Protocol

class Effect(Protocol):
    """Minimal protocol for type checking. Full ABC is Feature 6."""
    id: str

class EffectRegistry:
    _factories: dict[str, Callable[[], Effect]]
    _attack_registry: AttackRegistry

    def __init__(self, attack_registry: AttackRegistry) -> None: ...

    def register(self, id: str, factory: Callable[[], Effect]) -> None: ...
    def create(self, id: str) -> Effect: ...
    def unregister(self, id: str) -> None: ...
    def list_ids(self) -> list[str]: ...
```

| Method | Behavior |
|---|---|
| `register(id, factory)` | Adds factory to `_factories` keyed by `id`. Raises `ValueError` if ID already registered. |
| `create(id)` | Calls `_factories[id]()` and returns the fresh instance. Raises `KeyError` if ID not found. Each call returns a new independent object. |
| `unregister(id)` | Checks all attacks in `_attack_registry` for references in their `effect_ids`. If any reference this ID, raises `ValueError` listing the referencing attack IDs. Otherwise removes from `_factories`. Raises `KeyError` if ID not found. |
| `list_ids()` | Returns `list(_factories.keys())`. |

**Why factories, not instances:** Each effect application needs its own mutable state — remaining duration, source attacker reference, internal counters (SwitchCurse escalation). `create("burn")` called twice must return two independent objects. A factory (`Callable[[], Effect]`) guarantees this.

**Typing note:** EffectRegistry uses a `Protocol` or `Any` for the Effect return type in v1 since the Effect ABC (Feature 6) doesn't exist yet. When Feature 6 lands, update the type annotation. This is acceptable — registries are implemented before effects, and Python's duck typing handles it at runtime.

## 4. Construction order and wiring

Registries have a dependency chain for unregister integrity checks:

```
EffectRegistry → AttackRegistry → MiscritRegistry
```

Construction order:
```python
miscrit_reg = MiscritRegistry()
attack_reg = AttackRegistry(miscrit_registry=miscrit_reg)
effect_reg = EffectRegistry(attack_registry=attack_reg)
```

Population order (Feature 12, not this feature):
```python
# Effects registered first (in code, not config)
effect_reg.register("burn", lambda: Burn())
effect_reg.register("poison", lambda: Poison())

# Attacks second (from config) — their effect_ids must already be registered
attack_reg.register(fireball_attack)

# Miscrits last (from config) — their movelist attack_ids must already be registered
miscrit_reg.register(fire_sprite)
```

## 5. Testing strategy

### MiscritRegistry (`tests/unit/test_registries.py`)

| Test | Setup | Expected |
|---|---|---|
| Register and get | Register fire_sprite, get by ID | Returns same object |
| Register multiple, list_all | Register 3 miscrits | list_all returns 3 |
| list_by_nature | 2 fire miscrits, 1 water | list_by_nature(FIRE) returns 2 |
| list_by_nature dual | Miscrit with [FIRE, WIND] | Appears in both list_by_nature(FIRE) and list_by_nature(WIND) |
| list_by_rarity | 2 common, 1 rare | list_by_rarity(COMMON) returns 2 |
| Get unknown ID | Get "nonexistent" | KeyError |
| Register duplicate ID | Register same ID twice | ValueError |
| Unregister | Register then unregister | get raises KeyError |
| Unregister unknown | Unregister "nonexistent" | KeyError |
| list_all empty | Fresh registry | Returns [] |

### AttackRegistry (`tests/unit/test_registries.py`)

| Test | Setup | Expected |
|---|---|---|
| Register and get | Register fireball, get by ID | Returns same object |
| list_by_type | 2 elemental, 1 physical | list_by_type(ELEMENTAL) returns 2 |
| list_by_nature | 2 fire attacks, 1 water | list_by_nature(FIRE) returns 2 |
| list_by_nature physical | Physical attack (nature=None) | Not returned by any nature filter |
| Get unknown ID | Get "nonexistent" | KeyError |
| Register duplicate ID | Register same ID twice | ValueError |
| Unregister (no references) | Register attack, no miscrit uses it, unregister | Succeeds |
| Unregister (referenced by miscrit) | Register attack, register miscrit with it in movelist, unregister attack | ValueError listing miscrit ID |
| Unregister (referenced by multiple) | 2 miscrits reference it | ValueError listing both IDs |

### EffectRegistry (`tests/unit/test_registries.py`)

| Test | Setup | Expected |
|---|---|---|
| Register and create | Register factory, create | Returns object |
| Create twice → independent | Create "burn" twice, modify one | Other is unaffected |
| list_ids | Register 3 factories | list_ids returns 3 IDs |
| Create unknown ID | Create "nonexistent" | KeyError |
| Register duplicate ID | Register same ID twice | ValueError |
| Unregister (no references) | Register effect, no attack uses it, unregister | Succeeds |
| Unregister (referenced by attack) | Register effect, register attack with it in effect_ids, unregister effect | ValueError listing attack ID |

## 6. File mapping

| File | Purpose |
|---|---|
| `src/miscrits_clone/registries/miscrit_registry.py` | MiscritRegistry |
| `src/miscrits_clone/registries/attack_registry.py` | AttackRegistry (depends on MiscritRegistry) |
| `src/miscrits_clone/registries/effect_registry.py` | EffectRegistry (depends on AttackRegistry) |
| `tests/unit/test_registries.py` | All registry tests |

## 7. Outcome

After this feature:
- All three registries exist with `dict`-backed storage
- `register`/`get`/`list`/`unregister` work with clear error messages
- Referential integrity prevents orphaned references on unregister
- EffectRegistry produces independent instances from factories
- Registries are ready for Feature 12 (DataLoader) to populate them from config
