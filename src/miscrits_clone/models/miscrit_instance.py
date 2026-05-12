from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from miscrits_clone.models.enums import EffectCategory, Grade, Stat, StatQuality


@dataclass
class MiscritInstance:
    id: str
    template_id: str
    level: int
    grade: Grade
    stat_qualities: dict[Stat, StatQuality]
    resolved_stats: dict[Stat, int]
    _current_hp: int = field(init=False, repr=False)
    active_effects: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.id.strip()) == 0:
            raise ValueError("MiscritInstance id cannot be empty")
        if len(self.template_id.strip()) == 0:
            raise ValueError("MiscritInstance template_id cannot be empty")
        if not 1 <= self.level <= 35:
            raise ValueError(f"Level must be 1-35, got {self.level}")
        for stat in Stat:
            if stat not in self.resolved_stats:
                raise ValueError(f"resolved_stats must contain all 6 stats: missing {stat}")
            if self.resolved_stats[stat] <= 0:
                raise ValueError(f"resolved_stats[{stat}] must be positive, got {self.resolved_stats[stat]}")
            if stat not in self.stat_qualities:
                raise ValueError(f"stat_qualities must contain all 6 stats: missing {stat}")
        self._current_hp = self.resolved_stats[Stat.HP]

    @property
    def current_hp(self) -> int:
        return self._current_hp

    @current_hp.setter
    def current_hp(self, value: int) -> None:
        self._current_hp = max(0, min(value, self.max_hp))

    @property
    def max_hp(self) -> int:
        return self.resolved_stats[Stat.HP]

    @property
    def is_fainted(self) -> bool:
        return self._current_hp <= 0

    def add_effect(self, effect: Any) -> None:
        self.active_effects.append(effect)

    def remove_effect(self, effect: Any) -> None:
        if effect not in self.active_effects:
            raise ValueError("Effect not found in active_effects")
        self.active_effects.remove(effect)

    def tick_effects(self) -> list[Any]:
        expired: list[Any] = []
        remaining: list[Any] = []
        for effect in self.active_effects:
            effect.duration -= 1
            if effect.duration <= 0:
                expired.append(effect)
            else:
                remaining.append(effect)
        self.active_effects = remaining
        return expired

    def get_effects_by_category(self, category: EffectCategory) -> list[Any]:
        return [e for e in self.active_effects if e.category == category]
