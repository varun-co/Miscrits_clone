---
Status: Accepted
Date: 2026-05-10
Deciders: Varun
---

# ADR-0001: Use stdlib dataclasses over Pydantic for v1 domain models

## Context

Domain models (Miscrit, Attack, MiscritInstance, Battle, Player) need structured fields and construction-time validation. Two options:

1. **stdlib `dataclasses`** — validation in manual `__post_init__` methods
2. **Pydantic `BaseModel`** — declarative validation via type annotations, `Field()` constraints, and `@field_validator`

The TDD (§1.4) specifies "no runtime dependencies beyond stdlib for v1" to keep the package lean for RL training speed.

## Decision

Use stdlib dataclasses for all v1 domain models. Validation is manual via `__post_init__`.

## Rationale

**Why dataclasses for v1:**

- Zero dependencies — faster install, smaller containers, no Rust/C compilation issues across platforms
- RL training loops import the package thousands of times; eliminating Pydantic's ~50ms import overhead removes a variable
- v1 has only 5-6 validated models — the manual validation surface is small and manageable
- Native mypy support without plugins

**Why this may not hold for v2+:**

- Manual `__post_init__` is error-prone — v1 already had a bug where `len(self.name) == 2` was written instead of `len(self.natures) == 2`, caught only by tests
- Pydantic provides declarative validation (`Field(ge=1, le=5)`), which is harder to get wrong
- Feature 10 (Storage) requires serialization/deserialization — Pydantic gives this for free via `model_dump()` / `model_validate()`. With dataclasses, serialization must be built manually.
- v2 adds more models (team rosters, enchantments, evolution chains) increasing the manual validation surface
- Pydantic v2 (Rust core) is significantly faster than v1 — the performance gap with dataclasses has narrowed

## Consequences

- All v1 models use `@dataclass` (mutable) or `@dataclass(frozen=True)` (immutable)
- Validation logic lives in `__post_init__` methods and must be tested explicitly
- Serialization for Feature 10 must be built manually (JSON encode/decode per entity)
- If v2 introduces Pydantic, it is a migration of existing models — not a drop-in change. The migration scope is bounded (models only, no engine changes) but touches tests.

## Revisit trigger

Revisit this decision if any of the following occur:

- Feature 10 (Storage) serialization becomes painful to maintain manually
- v2 model count exceeds 10 validated entities
- A second validation bug is found that Pydantic's declarative style would have prevented
- RL training benchmarks show Pydantic import overhead is negligible relative to episode time
