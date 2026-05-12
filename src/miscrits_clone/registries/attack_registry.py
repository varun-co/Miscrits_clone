from __future__ import annotations

from typing import TYPE_CHECKING

from miscrits_clone.models.attack import Attack
from miscrits_clone.models.enums import AttackType, Nature

if TYPE_CHECKING:
    from miscrits_clone.registries.miscrit_registry import MiscritRegistry


class AttackRegistry:
    def __init__(self, miscrit_registry: MiscritRegistry) -> None:
        self._store: dict[str, Attack] = {}
        self._miscrit_registry = miscrit_registry

    def register(self, attack: Attack) -> None:
        if attack.id in self._store:
            raise ValueError(f"Attack '{attack.id}' is already registered")
        self._store[attack.id] = attack

    def get(self, id: str) -> Attack:
        if id not in self._store:
            raise KeyError(f"Attack '{id}' not found in registry")
        return self._store[id]

    def unregister(self, id: str) -> None:
        if id not in self._store:
            raise KeyError(f"Attack '{id}' not found in registry")
        referencing = [
            m.id
            for m in self._miscrit_registry.list_all()
            if m.has_attack(id)
        ]
        if referencing:
            raise ValueError(
                f"Cannot unregister attack '{id}': referenced by miscrits {referencing}"
            )
        del self._store[id]

    def list_all(self) -> list[Attack]:
        return list(self._store.values())

    def list_by_type(self, attack_type: AttackType) -> list[Attack]:
        return [a for a in self._store.values() if a.type == attack_type]

    def list_by_nature(self, nature: Nature) -> list[Attack]:
        return [a for a in self._store.values() if a.nature == nature]
