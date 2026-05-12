from miscrits_clone.models.enums import Nature, Rarity
from miscrits_clone.models.miscrit import Miscrit


class MiscritRegistry:
    def __init__(self) -> None:
        self._store: dict[str, Miscrit] = {}

    def register(self, miscrit: Miscrit) -> None:
        if miscrit.id in self._store:
            raise ValueError(f"Miscrit '{miscrit.id}' is already registered")
        self._store[miscrit.id] = miscrit

    def get(self, id: str) -> Miscrit:
        if id not in self._store:
            raise KeyError(f"Miscrit '{id}' not found in registry")
        return self._store[id]

    def unregister(self, id: str) -> None:
        if id not in self._store:
            raise KeyError(f"Miscrit '{id}' not found in registry")
        del self._store[id]

    def list_all(self) -> list[Miscrit]:
        return list(self._store.values())

    def list_by_nature(self, nature: Nature) -> list[Miscrit]:
        return [m for m in self._store.values() if nature in m.natures]

    def list_by_rarity(self, rarity: Rarity) -> list[Miscrit]:
        return [m for m in self._store.values() if m.rarity == rarity]
