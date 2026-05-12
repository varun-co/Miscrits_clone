from __future__ import annotations

import pytest

from miscrits_clone.models.attack import Attack
from miscrits_clone.models.battle import Battle, BattleSide, build_observation
from miscrits_clone.models.enums import (
    AttackType,
    BattleStatus,
    EffectCategory,
    Grade,
    Nature,
    Rarity,
    Stat,
    StatQuality,
)
from miscrits_clone.models.miscrit import Miscrit
from miscrits_clone.models.miscrit_instance import MiscritInstance
from miscrits_clone.models.value_types import Action, DamageResult, TurnEntry
from miscrits_clone.registries.attack_registry import AttackRegistry
from miscrits_clone.registries.miscrit_registry import MiscritRegistry


# ── Helpers ──────────────────────────────────────────────────────


def _all_stats(hp: int = 120, spd: int = 45, pd: int = 25, ed: int = 35, pa: int = 30, ea: int = 55) -> dict[Stat, int]:
    return {Stat.HP: hp, Stat.SPD: spd, Stat.PD: pd, Stat.ED: ed, Stat.PA: pa, Stat.EA: ea}


def _base_stats() -> dict[Stat, int]:
    return {s: 3 for s in Stat}


def _all_qualities() -> dict[Stat, StatQuality]:
    return {s: StatQuality.WHITE for s in Stat}


def _make_instance(id: str = "inst_a", template_id: str = "fire_sprite") -> MiscritInstance:
    return MiscritInstance(
        id=id,
        template_id=template_id,
        level=10,
        grade=Grade.B,
        stat_qualities=_all_qualities(),
        resolved_stats=_all_stats(),
    )


def _make_side(
    instance: MiscritInstance | None = None,
    player_id: str | None = "player_1",
) -> BattleSide:
    return BattleSide(
        player_id=player_id,
        active_miscrit=instance or _make_instance(),
        action_provider=None,
    )


def _make_battle(side_a: BattleSide | None = None, side_b: BattleSide | None = None) -> Battle:
    return Battle(
        id="battle_001",
        sides=[
            side_a or _make_side(player_id="p1"),
            side_b or _make_side(_make_instance(id="inst_b", template_id="water_serpent"), player_id="p2"),
        ],
    )


def _make_turn_entry(**overrides: object) -> TurnEntry:
    defaults: dict[str, object] = dict(
        round_number=1,
        actor_side=0,
        action=Action(attack_id="fireball"),
        hit=True,
        damage_result=DamageResult(raw_damage=50, nature_multiplier=1.0, final_damage=50, was_negated=False),
        hp_after=(120, 70),
        fainted=None,
        battle_ended=False,
    )
    defaults.update(overrides)
    return TurnEntry(**defaults)  # type: ignore[arg-type]


# ── BattleSide ───────────────────────────────────────────────────


class TestBattleSide:
    def test_creation(self) -> None:
        inst = _make_instance()
        side = BattleSide(player_id="p1", active_miscrit=inst, action_provider=None)
        assert side.player_id == "p1"
        assert side.active_miscrit is inst
        assert side.action_provider is None

    def test_null_player_id(self) -> None:
        side = BattleSide(player_id=None, active_miscrit=_make_instance(), action_provider=None)
        assert side.player_id is None


# ── Battle ───────────────────────────────────────────────────────


class TestBattle:
    def test_creation(self) -> None:
        b = _make_battle()
        assert b.round_number == 1
        assert b.status == BattleStatus.ACTIVE
        assert b.winner is None
        assert b.turn_log == []
        assert len(b.sides) == 2

    def test_log_turn(self) -> None:
        b = _make_battle()
        entry = _make_turn_entry()
        b.log_turn(entry)
        assert len(b.turn_log) == 1
        assert b.turn_log[0] is entry

    def test_log_turn_append_only(self) -> None:
        b = _make_battle()
        e1 = _make_turn_entry(round_number=1)
        e2 = _make_turn_entry(round_number=2)
        b.log_turn(e1)
        b.log_turn(e2)
        assert len(b.turn_log) == 2
        assert b.turn_log[0].round_number == 1
        assert b.turn_log[1].round_number == 2

    def test_complete(self) -> None:
        b = _make_battle()
        b.complete(b.sides[0])
        assert b.status == BattleStatus.COMPLETED
        assert b.winner is b.sides[0]

    def test_complete_already_completed(self) -> None:
        b = _make_battle()
        b.complete(b.sides[0])
        with pytest.raises(ValueError, match="already completed"):
            b.complete(b.sides[1])

    def test_complete_invalid_winner(self) -> None:
        b = _make_battle()
        outsider = _make_side(player_id="outsider")
        with pytest.raises(ValueError, match="must be one of"):
            b.complete(outsider)

    def test_get_opponent(self) -> None:
        b = _make_battle()
        assert b.get_opponent(b.sides[0]) is b.sides[1]
        assert b.get_opponent(b.sides[1]) is b.sides[0]

    def test_get_opponent_invalid(self) -> None:
        b = _make_battle()
        outsider = _make_side(player_id="outsider")
        with pytest.raises(ValueError, match="not part of this battle"):
            b.get_opponent(outsider)

    def test_get_side_index(self) -> None:
        b = _make_battle()
        assert b.get_side_index(b.sides[0]) == 0
        assert b.get_side_index(b.sides[1]) == 1

    def test_get_side_index_invalid(self) -> None:
        b = _make_battle()
        outsider = _make_side(player_id="outsider")
        with pytest.raises(ValueError, match="not part of this battle"):
            b.get_side_index(outsider)

    def test_invalid_one_side(self) -> None:
        with pytest.raises(ValueError, match="exactly 2 sides"):
            Battle(id="b1", sides=[_make_side()])

    def test_invalid_three_sides(self) -> None:
        with pytest.raises(ValueError, match="exactly 2 sides"):
            Battle(id="b1", sides=[_make_side(), _make_side(), _make_side()])

    def test_invalid_empty_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            Battle(id="", sides=[_make_side(), _make_side()])


# ── Observation builder ──────────────────────────────────────────


class _FakeEffect:
    def __init__(self, id: str = "burn", name: str = "Burn", category: EffectCategory = EffectCategory.DOT, duration: int = 3) -> None:
        self.id = id
        self.name = name
        self.category = category
        self.duration = duration


class TestBuildObservation:
    @pytest.fixture
    def registries(self) -> tuple[MiscritRegistry, AttackRegistry]:
        mr = MiscritRegistry()
        ar = AttackRegistry(miscrit_registry=mr)

        mr.register(Miscrit(
            id="fire_sprite",
            name="Fire Sprite",
            natures=[Nature.FIRE],
            rarity=Rarity.COMMON,
            base_stats=_base_stats(),
            movelist=["fireball", "tackle"],
        ))
        mr.register(Miscrit(
            id="water_serpent",
            name="Water Serpent",
            natures=[Nature.WATER],
            rarity=Rarity.COMMON,
            base_stats=_base_stats(),
            movelist=["splash"],
        ))

        ar.register(Attack(
            id="fireball", name="Fireball", description="Fire attack",
            type=AttackType.ELEMENTAL, nature=Nature.FIRE, power=50, accuracy=90,
        ))
        ar.register(Attack(
            id="tackle", name="Tackle", description="Physical attack",
            type=AttackType.PHYSICAL, nature=None, power=40, accuracy=95,
        ))
        ar.register(Attack(
            id="splash", name="Splash", description="Water attack",
            type=AttackType.ELEMENTAL, nature=Nature.WATER, power=45, accuracy=85,
        ))

        return mr, ar

    def test_own_side_full_visibility(self, registries: tuple[MiscritRegistry, AttackRegistry]) -> None:
        mr, ar = registries
        b = _make_battle()
        obs = build_observation(b, b.sides[0], ar, mr)

        assert obs.own_miscrit.template_id == "fire_sprite"
        assert obs.own_miscrit.natures == [Nature.FIRE]
        assert obs.own_miscrit.current_hp == 120
        assert obs.own_miscrit.max_hp == 120
        assert obs.own_miscrit.resolved_stats == _all_stats()
        assert obs.own_miscrit.base_resolved_stats == _all_stats()
        assert obs.own_miscrit.available_attacks == ["fireball", "tackle"]

    def test_opponent_limited_visibility(self, registries: tuple[MiscritRegistry, AttackRegistry]) -> None:
        mr, ar = registries
        b = _make_battle()
        obs = build_observation(b, b.sides[0], ar, mr)

        assert obs.opponent_miscrit.template_id == "water_serpent"
        assert obs.opponent_miscrit.natures == [Nature.WATER]
        assert obs.opponent_miscrit.current_hp == 120
        assert obs.opponent_miscrit.max_hp == 120
        assert obs.opponent_miscrit.stats_visible is False
        assert obs.opponent_miscrit.resolved_stats is None

    def test_round_number_and_turn_log(self, registries: tuple[MiscritRegistry, AttackRegistry]) -> None:
        mr, ar = registries
        b = _make_battle()
        b.round_number = 3
        b.log_turn(_make_turn_entry(round_number=1))
        b.log_turn(_make_turn_entry(round_number=2))
        obs = build_observation(b, b.sides[0], ar, mr)
        assert obs.round_number == 3
        assert len(obs.turn_log) == 2

    def test_own_effects_visible(self, registries: tuple[MiscritRegistry, AttackRegistry]) -> None:
        mr, ar = registries
        b = _make_battle()
        b.sides[0].active_miscrit.add_effect(_FakeEffect(id="burn", name="Burn", duration=2))
        obs = build_observation(b, b.sides[0], ar, mr)
        assert len(obs.own_miscrit.active_effects) == 1
        assert obs.own_miscrit.active_effects[0].effect_id == "burn"

    def test_opponent_effects_visible(self, registries: tuple[MiscritRegistry, AttackRegistry]) -> None:
        mr, ar = registries
        b = _make_battle()
        b.sides[1].active_miscrit.add_effect(_FakeEffect(id="poison", name="Poison", duration=4))
        obs = build_observation(b, b.sides[0], ar, mr)
        assert len(obs.opponent_miscrit.active_effects) == 1
        assert obs.opponent_miscrit.active_effects[0].effect_id == "poison"

    def test_turn_log_is_copy(self, registries: tuple[MiscritRegistry, AttackRegistry]) -> None:
        mr, ar = registries
        b = _make_battle()
        b.log_turn(_make_turn_entry())
        obs = build_observation(b, b.sides[0], ar, mr)
        b.log_turn(_make_turn_entry(round_number=2))
        assert len(obs.turn_log) == 1
