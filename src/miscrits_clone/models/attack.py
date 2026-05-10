from dataclasses import dataclass, field
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

    def __post_init__(self) -> None:
        if self.type == AttackType.ELEMENTAL and self.nature is None:
            raise ValueError("Elemental attack must have a nature")

        if self.type == AttackType.PHYSICAL and self.nature is not None:
            raise ValueError("Physical attack must not have a nature")

        if self.power <= 0:
            raise ValueError(f"Attack power must be positive, got {self.power}")

        if not 0 <= self.accuracy <= 100:
            raise ValueError(f"Attack accuracy must be 0-100, got {self.accuracy}")

        if len(self.id.strip()) == 0:
            raise ValueError("Attack id cannot be empty")

        if len(self.name.strip()) == 0:
            raise ValueError("Attack name cannot be empty")
