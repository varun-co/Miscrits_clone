from dataclasses import dataclass, field
from miscrits_clone.models.enums import Nature, Stat, Rarity


@dataclass
class Miscrit:
    id: str
    name: str
    natures: list[Nature]
    rarity: Rarity
    base_stats: dict[Stat, int]
    movelist: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.natures) < 1:
            raise ValueError("Miscrit must have at least 1 nature")

        if len(self.natures) > 2:
            raise ValueError("Miscrit cannot have more than 2 natures")

        if len(self.natures) == 2:
            first_nature, second_nature = self.natures
            if first_nature.is_triangle_1 == second_nature.is_triangle_1:
                raise ValueError(
                    "Dual-natured miscrit must have one nature from each triangle"
                )
            elif not first_nature.is_triangle_1:
                self.natures = [second_nature, first_nature]

        for stat in set(Stat):
            if stat not in self.base_stats.keys():
                raise ValueError(f"base_stats must contain all 6 stats: {stat}")

        for stat, value in self.base_stats.items():
            if not 1 <= value <= 5:
                raise ValueError(
                    f"base_stat {stat} must be between 1 and 5, got {value}"
                )

        if len(self.id.strip()) == 0:
            raise ValueError("Miscrit id cannot be empty")

        if len(self.name.strip()) == 0:
            raise ValueError("Miscrit name cannot be empty")

    def add_attack(self, attack_id: str) -> None:
        if attack_id in self.movelist:
            raise ValueError(f"Attack '{attack_id}' already exists in movelist")
        self.movelist.append(attack_id)

    def remove_attack(self, attack_id: str) -> None:
        if attack_id not in self.movelist:
            raise ValueError(f"Attack '{attack_id}' not found in movelist")
        self.movelist.remove(attack_id)

    def replace_attack(self, old_attack_id: str, new_attack_id: str) -> None:
        if old_attack_id not in self.movelist:
            raise ValueError(f"Attack '{old_attack_id}' not found in movelist")
        if new_attack_id in self.movelist:
            raise ValueError(f"Attack '{new_attack_id}' already exists in movelist")
        idx = self.movelist.index(old_attack_id)
        self.movelist[idx] = new_attack_id

    def has_attack(self, attack_id: str) -> bool:
        return attack_id in self.movelist
