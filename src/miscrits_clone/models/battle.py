from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from miscrits_clone.models.enums import BattleStatus, Stat
from miscrits_clone.models.miscrit_instance import MiscritInstance
from miscrits_clone.models.value_types import (
    BattleObservation,
    EffectSummary,
    ObservedMiscrit,
    OpponentObservation,
    TurnEntry,
)

if TYPE_CHECKING:
    from miscrits_clone.registries.attack_registry import AttackRegistry
    from miscrits_clone.registries.miscrit_registry import MiscritRegistry


@dataclass
class BattleSide:
    player_id: str | None
    active_miscrit: MiscritInstance
    action_provider: Any


@dataclass
class Battle:
    id: str
    sides: list[BattleSide]
    round_number: int = 1
    turn_log: list[TurnEntry] = field(default_factory=list)
    status: BattleStatus = BattleStatus.ACTIVE
    winner: BattleSide | None = None

    def __post_init__(self) -> None:
        if len(self.id.strip()) == 0:
            raise ValueError("Battle id cannot be empty")
        if len(self.sides) != 2:
            raise ValueError(f"Battle must have exactly 2 sides, got {len(self.sides)}")

    def log_turn(self, entry: TurnEntry) -> None:
        self.turn_log.append(entry)

    def complete(self, winner: BattleSide) -> None:
        if self.status == BattleStatus.COMPLETED:
            raise ValueError("Battle is already completed")
        if winner not in self.sides:
            raise ValueError("Winner must be one of the battle's sides")
        self.status = BattleStatus.COMPLETED
        self.winner = winner

    def get_opponent(self, side: BattleSide) -> BattleSide:
        if side is self.sides[0]:
            return self.sides[1]
        if side is self.sides[1]:
            return self.sides[0]
        raise ValueError("Side is not part of this battle")

    def get_side_index(self, side: BattleSide) -> int:
        if side is self.sides[0]:
            return 0
        if side is self.sides[1]:
            return 1
        raise ValueError("Side is not part of this battle")


def build_observation(
    battle: Battle,
    requesting_side: BattleSide,
    attack_registry: AttackRegistry,
    miscrit_registry: MiscritRegistry,
) -> BattleObservation:
    opponent_side = battle.get_opponent(requesting_side)

    own = requesting_side.active_miscrit
    own_template = miscrit_registry.get(own.template_id)
    attack_ids = own_template.movelist
    own_effects = [
        EffectSummary(
            effect_id=e.id,
            name=e.name,
            category=e.category,
            remaining_duration=e.duration,
        )
        for e in own.active_effects
    ]

    own_observed = ObservedMiscrit(
        template_id=own.template_id,
        natures=list(own_template.natures),
        current_hp=own.current_hp,
        max_hp=own.max_hp,
        resolved_stats=dict(own.resolved_stats),
        base_resolved_stats=dict(own.resolved_stats),
        active_effects=own_effects,
        available_attacks=list(attack_ids),
    )

    opp = opponent_side.active_miscrit
    opp_template = miscrit_registry.get(opp.template_id)
    opp_effects = [
        EffectSummary(
            effect_id=e.id,
            name=e.name,
            category=e.category,
            remaining_duration=e.duration,
        )
        for e in opp.active_effects
    ]

    opp_observed = OpponentObservation(
        template_id=opp.template_id,
        natures=list(opp_template.natures),
        current_hp=opp.current_hp,
        max_hp=opp.max_hp,
        active_effects=opp_effects,
        stats_visible=False,
        resolved_stats=None,
    )

    return BattleObservation(
        own_miscrit=own_observed,
        opponent_miscrit=opp_observed,
        round_number=battle.round_number,
        turn_log=list(battle.turn_log),
    )
