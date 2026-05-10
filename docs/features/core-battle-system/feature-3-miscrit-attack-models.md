---
Status: Draft
Owner: Varun
Last updated: 2026-05-08
References: docs/features/core-battle-system/tdd.md §2.3, Issue #3, Issue #13
---

# Feature 3: Miscrit Template and Attack Data Models

## 1. Problem statement

Battles need miscrits and attacks as structured data. Registries (Feature 4) will store them, the engine will read them. These are pure data entities — no behavior beyond validation and movelist management. Invalid data must be caught at construction time, not at battle runtime where it would cause confusing failures.

## 2. Miscrit template (`src/miscrits_clone/models/miscrit.py`)

A **mutable** dataclass. Mutable because movelist CRUD modifies it after construction (templates are built up at startup, then read-only during battles). Validation runs in `__post_init__`.

### 2.1 Class definition

```python
from dataclasses import dataclass, field
from typing import Optional
from miscrits_clone.models.enums import Nature, Stat, Rarity, TRIANGLE_1

@dataclass
class Miscrit:
    id: str
    name: str
    natures: list[Nature]
    rarity: Rarity
    base_stats: dict[Stat, int]
    movelist: list[str] = field(default_factory=list)

    def __post_init__(self) -> None: ...

    # --- Movelist CRUD ---

    def add_attack(self, attack_id: str) -> None: ...

    def remove_attack(self, attack_id: str) -> None: ...

    def replace_attack(self, old_attack_id: str, new_attack_id: str) -> None: ...

    def has_attack(self, attack_id: str) -> bool: ...
```

### 2.2 `__post_init__` validation rules

Runs on every construction. Raises `ValueError` with a descriptive message on failure.

| Rule | Check | Error message pattern |
|---|---|---|
| Non-empty natures | `len(natures) >= 1` | `"Miscrit must have at least 1 nature"` |
| Max 2 natures | `len(natures) <= 2` | `"Miscrit cannot have more than 2 natures"` |
| Dual-nature: different triangles | If 2 natures, they must not both be in `TRIANGLE_1` or both outside it | `"Dual-natured miscrit must have one nature from each triangle"` |
| Dual-nature: auto-sort order | If 2 natures and first is not from Triangle 1, swap them silently. After sort: index 0 = Triangle 1, index 1 = Triangle 2 | *(no error — auto-corrects)* |
| All 6 base_stats present | `set(base_stats.keys()) == set(Stat)` | `"base_stats must contain all 6 stats: {missing}"` |
| base_stats range | All values `1 <= v <= 5` | `"base_stat {stat} must be between 1 and 5, got {v}"` |
| Non-empty id | `len(id.strip()) > 0` | `"Miscrit id cannot be empty"` |
| Non-empty name | `len(name.strip()) > 0` | `"Miscrit name cannot be empty"` |

**Dual-nature auto-sort logic:**

```
if len(natures) == 2:
    if natures[0] not in TRIANGLE_1 and natures[1] in TRIANGLE_1:
        natures = [natures[1], natures[0]]   # swap to [T1, T2]
    elif natures[0] not in TRIANGLE_1 and natures[1] not in TRIANGLE_1:
        raise ValueError(...)  # both Triangle 2
    elif natures[0] in TRIANGLE_1 and natures[1] in TRIANGLE_1:
        raise ValueError(...)  # both Triangle 1
```

Auto-sort happens **before** the triangle validation check, so `[WIND, FIRE]` becomes `[FIRE, WIND]` without error. The ordering convention (Triangle 1 first, Triangle 2 second) is enforced here — the NatureResolver relies on it at runtime.

### 2.3 Movelist CRUD methods

| Method | Signature | Behavior |
|---|---|---|
| `add_attack` | `(self, attack_id: str) -> None` | Appends `attack_id` to `self.movelist`. Raises `ValueError` if already present (no duplicates). |
| `remove_attack` | `(self, attack_id: str) -> None` | Removes `attack_id` from `self.movelist`. Raises `ValueError` if not found. |
| `replace_attack` | `(self, old_attack_id: str, new_attack_id: str) -> None` | Replaces `old_attack_id` with `new_attack_id` at the same index. Raises `ValueError` if `old_attack_id` not found. Raises `ValueError` if `new_attack_id` already present. |
| `has_attack` | `(self, attack_id: str) -> bool` | Returns `True` if `attack_id` is in `self.movelist`. |

**Why no cross-validation with AttackRegistry here:** The template is pure data. It stores attack ID strings. Whether those IDs correspond to real attacks is the registry's job (Feature 4). This avoids a circular dependency between models and registries.

---

## 3. Attack entity (`src/miscrits_clone/models/attack.py`)

A **frozen** dataclass. Attacks are immutable after construction — power, accuracy, effects never change at runtime. Validation runs in `__post_init__`.

### 3.1 Class definition

```python
from dataclasses import dataclass, field
from typing import Optional
from miscrits_clone.models.enums import AttackType, Nature, TargetRule

@dataclass(frozen=True, kw_only=True)
class Attack:
    id: str
    name: str
    description: str
    type: AttackType
    nature: Nature | None
    power: int
    accuracy: int
    effect_ids: list[str] = field(default_factory=list)
    target_rule: TargetRule = TargetRule.SINGLE_OPPONENT

    def __post_init__(self) -> None: ...
```

### 3.2 `__post_init__` validation rules

| Rule | Check | Error message pattern |
|---|---|---|
| Elemental needs nature | If `type == ELEMENTAL`, `nature` must not be `None` | `"Elemental attack must have a nature"` |
| Physical has no nature | If `type == PHYSICAL`, `nature` must be `None` | `"Physical attack must not have a nature"` |
| Power positive | `power > 0` | `"Attack power must be positive, got {power}"` |
| Accuracy range | `0 <= accuracy <= 100` | `"Attack accuracy must be 0-100, got {accuracy}"` |
| Non-empty id | `len(id.strip()) > 0` | `"Attack id cannot be empty"` |
| Non-empty name | `len(name.strip()) > 0` | `"Attack name cannot be empty"` |

**Note on `__post_init__` with frozen dataclass:** Since the dataclass is frozen, `__post_init__` cannot assign fields normally. Use `object.__setattr__` if any transformation is needed, but for Attack all validation is read-only checks (no mutation), so standard `__post_init__` works.

---

## 4. What this feature does NOT include

- **MiscritInstance** — owned creature with mutable HP, effects, level. That's Feature 5.
- **Registries** — storing and querying templates/attacks. That's Feature 4.
- **Attack-to-nature validation against movelist** — verifying that a miscrit's attacks match its natures is a registry concern (Feature 4), not a data model concern.
- **Effect entities** — the Effect ABC is Feature 6.

---

## 5. Testing strategy

### 5.1 Miscrit tests (`tests/unit/test_miscrit.py`)

| Test | Input | Expected |
|---|---|---|
| Valid single-nature | `natures=[FIRE]` | Construction succeeds, all fields accessible |
| Valid dual-nature same order | `natures=[FIRE, WIND]` | Accepted, stored as `[FIRE, WIND]` |
| Valid dual-nature auto-sorted | `natures=[WIND, FIRE]` | Accepted, stored as `[FIRE, WIND]` |
| Reject empty natures | `natures=[]` | `ValueError` |
| Reject 3 natures | `natures=[FIRE, WATER, WIND]` | `ValueError` |
| Reject same triangle (T1) | `natures=[FIRE, WATER]` | `ValueError` |
| Reject same triangle (T2) | `natures=[WIND, EARTH]` | `ValueError` |
| All 6 base_stats required | Missing `HP` | `ValueError` |
| base_stat out of range (0) | `{HP: 0, ...}` | `ValueError` |
| base_stat out of range (6) | `{HP: 6, ...}` | `ValueError` |
| Empty id rejected | `id=""` | `ValueError` |
| Empty name rejected | `name=""` | `ValueError` |
| Movelist: add_attack | Add `"fireball"` | `movelist == ["fireball"]` |
| Movelist: add duplicate rejected | Add `"fireball"` twice | `ValueError` on second add |
| Movelist: remove_attack | Add then remove `"fireball"` | `movelist == []` |
| Movelist: remove missing rejected | Remove `"fireball"` from empty | `ValueError` |
| Movelist: replace_attack | `["a", "b"]` → replace `"a"` with `"c"` | `["c", "b"]` |
| Movelist: replace preserves order | `["a", "b", "c"]` → replace `"b"` with `"x"` | `["a", "x", "c"]` |
| Movelist: replace missing old rejected | Replace `"z"` (not present) | `ValueError` |
| Movelist: replace duplicate new rejected | `["a", "b"]` → replace `"a"` with `"b"` | `ValueError` |
| Movelist: has_attack true | Add `"fireball"`, check | `True` |
| Movelist: has_attack false | Empty movelist, check | `False` |
| Movelist starts empty by default | No movelist arg | `movelist == []` |

### 5.2 Attack tests (`tests/unit/test_attack.py`)

| Test | Input | Expected |
|---|---|---|
| Valid physical attack | `type=PHYSICAL, nature=None` | Construction succeeds |
| Valid elemental attack | `type=ELEMENTAL, nature=FIRE` | Construction succeeds |
| Reject elemental with null nature | `type=ELEMENTAL, nature=None` | `ValueError` |
| Reject physical with nature | `type=PHYSICAL, nature=FIRE` | `ValueError` |
| Reject accuracy < 0 | `accuracy=-1` | `ValueError` |
| Reject accuracy > 100 | `accuracy=150` | `ValueError` |
| Accuracy boundary 0 accepted | `accuracy=0` | Accepted |
| Accuracy boundary 100 accepted | `accuracy=100` | Accepted |
| Reject power = 0 | `power=0` | `ValueError` |
| Reject power negative | `power=-5` | `ValueError` |
| Power = 1 accepted | `power=1` | Accepted |
| Empty id rejected | `id=""` | `ValueError` |
| Empty name rejected | `name=""` | `ValueError` |
| Attack is frozen | Assign `attack.power = 10` | `FrozenInstanceError` |
| Default effect_ids is empty list | No effect_ids arg | `effect_ids == []` |
| Default target_rule is SINGLE_OPPONENT | No target_rule arg | `target_rule == SINGLE_OPPONENT` |

---

## 6. File mapping

| File | Purpose |
|---|---|
| `src/miscrits_clone/models/miscrit.py` | `Miscrit` dataclass with validation + movelist CRUD |
| `src/miscrits_clone/models/attack.py` | `Attack` frozen dataclass with validation |
| `tests/unit/test_miscrit.py` | Template construction, validation, movelist CRUD |
| `tests/unit/test_attack.py` | Attack construction, validation, immutability |

## 7. Outcome

After this feature:
- Miscrit species can be defined with validated natures, base_stats, and managed movelists
- Attacks can be defined with validated type/nature consistency, power, and accuracy
- Dual-nature ordering convention (T1 first, T2 second) is enforced at construction — NatureResolver can rely on it
- Invalid configurations are caught at construction with descriptive `ValueError` messages
- All types importable from `miscrits_clone.models.miscrit` and `miscrits_clone.models.attack`
