from dataclasses import dataclass, field
from typing import Optional, List
from .enums import Nature, Stat, Grade, AttackType, EffectCategory, TargetRule


@dataclass(frozen=True, kw_only=True)
class DamageResult:
    raw_damage: int
    nature_multiplier: float
    final_damage: int
    was_negated: bool


@dataclass(frozen=True, kw_only=True)
class Slot:
    index: int
    miscrit_instance_id: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class Action:
    attack_id: str


@dataclass(frozen=True, kw_only=True)
class EffectSummary:
    effect_id: str
    name: str
    category: EffectCategory
    remaining_duration: int


@dataclass(frozen=True, kw_only=True)
class TurnEntry:
    round_number: int
    actor_side: int  # 0 or 1, index into battle.sides
    action: Action | None
    hit: bool | None  # None if fainted before acting
    damage_result: Optional[DamageResult]
    effects_applied: List[EffectSummary] = field(default_factory=list)
    effects_triggered: List[EffectSummary] = field(default_factory=list)
    effects_expired: List[EffectSummary] = field(default_factory=list)
    hp_after: tuple[int, int]
    fainted: int | None
    battle_ended: bool


@dataclass(frozen=True, kw_only=True)
class ObservedMiscrit:
    template_id: str
    natures: List[Nature]
    current_hp: int
    max_hp: int
    resolved_stats: dict[Stat, int]
    base_resolved_stats: dict[Stat, int]
    active_effects: List[EffectSummary]
    available_attacks: List[str]


@dataclass(frozen=True, kw_only=True)
class OpponentObservation:
    template_id: str
    natures: List[Nature]
    current_hp: int
    max_hp: int
    active_effects: List[EffectSummary]
    stats_visible: bool
    resolved_stats: Optional[dict[Stat, int]] = None


@dataclass(frozen=True, kw_only=True)
class BattleObservation:
    own_miscrit: ObservedMiscrit
    opponent_miscrit: OpponentObservation
    round_number: int
    turn_log: List[TurnEntry]


@dataclass(frozen=True, kw_only=True)
class BattleResult:
    winner_side: int | None
    turn_log: List[TurnEntry]
    total_rounds: int
