from __future__ import annotations

import pytest

from miscrits_clone.models.attack import Attack
from miscrits_clone.models.enums import (
    AttackType,
    Nature,
    Rarity,
    Stat,
)
from miscrits_clone.models.miscrit import Miscrit
from miscrits_clone.registries.attack_registry import AttackRegistry
from miscrits_clone.registries.effect_registry import EffectRegistry
from miscrits_clone.registries.miscrit_registry import MiscritRegistry


# ── Helpers ──────────────────────────────────────────────────────


def _all_stats(hp: int = 3, spd: int = 3, pd: int = 3, ed: int = 3, pa: int = 3, ea: int = 3) -> dict[Stat, int]:
    return {Stat.HP: hp, Stat.SPD: spd, Stat.PD: pd, Stat.ED: ed, Stat.PA: pa, Stat.EA: ea}


def _make_miscrit(id: str = "fire_sprite", name: str = "Fire Sprite", natures: list[Nature] | None = None, rarity: Rarity = Rarity.COMMON) -> Miscrit:
    return Miscrit(
        id=id,
        name=name,
        natures=natures or [Nature.FIRE],
        rarity=rarity,
        base_stats=_all_stats(),
    )


def _make_elemental(id: str = "fireball", name: str = "Fireball", nature: Nature = Nature.FIRE, effect_ids: list[str] | None = None) -> Attack:
    return Attack(
        id=id,
        name=name,
        description="A ball of fire",
        type=AttackType.ELEMENTAL,
        nature=nature,
        power=50,
        accuracy=90,
        effect_ids=effect_ids or [],
    )


def _make_physical(id: str = "tackle", name: str = "Tackle", effect_ids: list[str] | None = None) -> Attack:
    return Attack(
        id=id,
        name=name,
        description="A basic tackle",
        type=AttackType.PHYSICAL,
        nature=None,
        power=40,
        accuracy=95,
        effect_ids=effect_ids or [],
    )


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def miscrit_reg() -> MiscritRegistry:
    return MiscritRegistry()


@pytest.fixture
def attack_reg(miscrit_reg: MiscritRegistry) -> AttackRegistry:
    return AttackRegistry(miscrit_registry=miscrit_reg)


@pytest.fixture
def effect_reg(attack_reg: AttackRegistry) -> EffectRegistry:
    return EffectRegistry(attack_registry=attack_reg)


# ── MiscritRegistry ─────────────────────────────────────────────


class TestMiscritRegistry:
    def test_register_and_get(self, miscrit_reg: MiscritRegistry) -> None:
        m = _make_miscrit()
        miscrit_reg.register(m)
        assert miscrit_reg.get("fire_sprite") is m

    def test_register_multiple_list_all(self, miscrit_reg: MiscritRegistry) -> None:
        for id in ("a", "b", "c"):
            miscrit_reg.register(_make_miscrit(id=id, name=id))
        assert len(miscrit_reg.list_all()) == 3

    def test_list_by_nature(self, miscrit_reg: MiscritRegistry) -> None:
        miscrit_reg.register(_make_miscrit(id="f1", name="F1", natures=[Nature.FIRE]))
        miscrit_reg.register(_make_miscrit(id="f2", name="F2", natures=[Nature.FIRE]))
        miscrit_reg.register(_make_miscrit(id="w1", name="W1", natures=[Nature.WATER]))
        assert len(miscrit_reg.list_by_nature(Nature.FIRE)) == 2
        assert len(miscrit_reg.list_by_nature(Nature.WATER)) == 1

    def test_list_by_nature_dual(self, miscrit_reg: MiscritRegistry) -> None:
        miscrit_reg.register(_make_miscrit(id="dual", name="Dual", natures=[Nature.FIRE, Nature.WIND]))
        assert len(miscrit_reg.list_by_nature(Nature.FIRE)) == 1
        assert len(miscrit_reg.list_by_nature(Nature.WIND)) == 1

    def test_list_by_rarity(self, miscrit_reg: MiscritRegistry) -> None:
        miscrit_reg.register(_make_miscrit(id="c1", name="C1", rarity=Rarity.COMMON))
        miscrit_reg.register(_make_miscrit(id="c2", name="C2", rarity=Rarity.COMMON))
        miscrit_reg.register(_make_miscrit(id="r1", name="R1", rarity=Rarity.RARE))
        assert len(miscrit_reg.list_by_rarity(Rarity.COMMON)) == 2
        assert len(miscrit_reg.list_by_rarity(Rarity.RARE)) == 1

    def test_get_unknown_raises(self, miscrit_reg: MiscritRegistry) -> None:
        with pytest.raises(KeyError, match="not found"):
            miscrit_reg.get("nonexistent")

    def test_register_duplicate_raises(self, miscrit_reg: MiscritRegistry) -> None:
        miscrit_reg.register(_make_miscrit())
        with pytest.raises(ValueError, match="already registered"):
            miscrit_reg.register(_make_miscrit())

    def test_unregister(self, miscrit_reg: MiscritRegistry) -> None:
        miscrit_reg.register(_make_miscrit())
        miscrit_reg.unregister("fire_sprite")
        with pytest.raises(KeyError):
            miscrit_reg.get("fire_sprite")

    def test_unregister_unknown_raises(self, miscrit_reg: MiscritRegistry) -> None:
        with pytest.raises(KeyError, match="not found"):
            miscrit_reg.unregister("nonexistent")

    def test_list_all_empty(self, miscrit_reg: MiscritRegistry) -> None:
        assert miscrit_reg.list_all() == []

    def test_list_by_nature_no_match(self, miscrit_reg: MiscritRegistry) -> None:
        miscrit_reg.register(_make_miscrit(id="f1", name="F1", natures=[Nature.FIRE]))
        assert miscrit_reg.list_by_nature(Nature.WATER) == []


# ── AttackRegistry ───────────────────────────────────────────────


class TestAttackRegistry:
    def test_register_and_get(self, attack_reg: AttackRegistry) -> None:
        a = _make_elemental()
        attack_reg.register(a)
        assert attack_reg.get("fireball") is a

    def test_list_by_type(self, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental(id="e1", name="E1"))
        attack_reg.register(_make_elemental(id="e2", name="E2"))
        attack_reg.register(_make_physical(id="p1", name="P1"))
        assert len(attack_reg.list_by_type(AttackType.ELEMENTAL)) == 2
        assert len(attack_reg.list_by_type(AttackType.PHYSICAL)) == 1

    def test_list_by_nature(self, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental(id="f1", name="F1", nature=Nature.FIRE))
        attack_reg.register(_make_elemental(id="f2", name="F2", nature=Nature.FIRE))
        attack_reg.register(_make_elemental(id="w1", name="W1", nature=Nature.WATER))
        assert len(attack_reg.list_by_nature(Nature.FIRE)) == 2
        assert len(attack_reg.list_by_nature(Nature.WATER)) == 1

    def test_list_by_nature_excludes_physical(self, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_physical())
        assert len(attack_reg.list_by_nature(Nature.FIRE)) == 0

    def test_get_unknown_raises(self, attack_reg: AttackRegistry) -> None:
        with pytest.raises(KeyError, match="not found"):
            attack_reg.get("nonexistent")

    def test_register_duplicate_raises(self, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental())
        with pytest.raises(ValueError, match="already registered"):
            attack_reg.register(_make_elemental())

    def test_unregister_no_references(self, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental())
        attack_reg.unregister("fireball")
        with pytest.raises(KeyError):
            attack_reg.get("fireball")

    def test_unregister_referenced_by_miscrit(self, miscrit_reg: MiscritRegistry, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental())
        m = _make_miscrit()
        m.add_attack("fireball")
        miscrit_reg.register(m)
        with pytest.raises(ValueError, match="referenced by miscrits"):
            attack_reg.unregister("fireball")

    def test_unregister_referenced_by_multiple(self, miscrit_reg: MiscritRegistry, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental())
        m1 = _make_miscrit(id="m1", name="M1")
        m1.add_attack("fireball")
        m2 = _make_miscrit(id="m2", name="M2")
        m2.add_attack("fireball")
        miscrit_reg.register(m1)
        miscrit_reg.register(m2)
        with pytest.raises(ValueError, match="referenced by miscrits") as exc_info:
            attack_reg.unregister("fireball")
        assert "m1" in str(exc_info.value)
        assert "m2" in str(exc_info.value)

    def test_unregister_then_reregister(self, attack_reg: AttackRegistry) -> None:
        attack_reg.register(_make_elemental())
        attack_reg.unregister("fireball")
        attack_reg.register(_make_elemental())
        assert attack_reg.get("fireball").name == "Fireball"

    def test_unregister_unknown_raises(self, attack_reg: AttackRegistry) -> None:
        with pytest.raises(KeyError, match="not found"):
            attack_reg.unregister("nonexistent")


# ── EffectRegistry ───────────────────────────────────────────────


class _FakeEffect:
    def __init__(self) -> None:
        self.counter = 0


class TestEffectRegistry:
    def test_register_and_create(self, effect_reg: EffectRegistry) -> None:
        effect_reg.register("burn", _FakeEffect)
        obj = effect_reg.create("burn")
        assert isinstance(obj, _FakeEffect)

    def test_create_twice_independent(self, effect_reg: EffectRegistry) -> None:
        effect_reg.register("burn", _FakeEffect)
        a = effect_reg.create("burn")
        b = effect_reg.create("burn")
        a.counter = 99
        assert b.counter == 0

    def test_list_ids(self, effect_reg: EffectRegistry) -> None:
        for id in ("burn", "poison", "heal"):
            effect_reg.register(id, _FakeEffect)
        assert sorted(effect_reg.list_ids()) == ["burn", "heal", "poison"]

    def test_create_unknown_raises(self, effect_reg: EffectRegistry) -> None:
        with pytest.raises(KeyError, match="not found"):
            effect_reg.create("nonexistent")

    def test_register_duplicate_raises(self, effect_reg: EffectRegistry) -> None:
        effect_reg.register("burn", _FakeEffect)
        with pytest.raises(ValueError, match="already registered"):
            effect_reg.register("burn", _FakeEffect)

    def test_unregister_no_references(self, effect_reg: EffectRegistry) -> None:
        effect_reg.register("burn", _FakeEffect)
        effect_reg.unregister("burn")
        with pytest.raises(KeyError):
            effect_reg.create("burn")

    def test_unregister_referenced_by_attack(self, attack_reg: AttackRegistry, effect_reg: EffectRegistry) -> None:
        effect_reg.register("burn", _FakeEffect)
        attack_reg.register(_make_elemental(effect_ids=["burn"]))
        with pytest.raises(ValueError, match="referenced by attacks"):
            effect_reg.unregister("burn")

    def test_unregister_unknown_raises(self, effect_reg: EffectRegistry) -> None:
        with pytest.raises(KeyError, match="not found"):
            effect_reg.unregister("nonexistent")
