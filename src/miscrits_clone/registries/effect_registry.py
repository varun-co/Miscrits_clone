from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from miscrits_clone.registries.attack_registry import AttackRegistry


class EffectRegistry:
    def __init__(self, attack_registry: AttackRegistry) -> None:
        self._factories: dict[str, Callable[[], Any]] = {}
        self._attack_registry = attack_registry

    def register(self, id: str, factory: Callable[[], Any]) -> None:
        if id in self._factories:
            raise ValueError(f"Effect '{id}' is already registered")
        self._factories[id] = factory

    def create(self, id: str) -> Any:
        if id not in self._factories:
            raise KeyError(f"Effect '{id}' not found in registry")
        return self._factories[id]()

    def unregister(self, id: str) -> None:
        if id not in self._factories:
            raise KeyError(f"Effect '{id}' not found in registry")
        referencing = [
            a.id
            for a in self._attack_registry.list_all()
            if id in a.effect_ids
        ]
        if referencing:
            raise ValueError(
                f"Cannot unregister effect '{id}': referenced by attacks {referencing}"
            )
        del self._factories[id]

    def list_ids(self) -> list[str]:
        return list(self._factories.keys())
