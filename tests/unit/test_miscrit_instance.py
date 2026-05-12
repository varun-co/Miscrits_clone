from __future__ import annotations

import pytest

from miscrits_clone.models.enums import EffectCategory, Grade, Stat, StatQuality
from miscrits_clone.models.miscrit_instance import MiscritInstance


# ── Helpers ──────────────────────────────────────────────────────


def _all_stats(hp: int = 120, spd: int = 45, pd: int = 25, ed: int = 35, pa: int = 30, ea: int = 55) -> dict[Stat, int]:
    return {Stat.HP: hp, Stat.SPD: spd, Stat.PD: pd, Stat.ED: ed, Stat.PA: pa, Stat.EA: ea}


def _all_qualities() -> dict[Stat, StatQuality]:
    return {s: StatQuality.WHITE for s in Stat}


def _make_instance(**overrides: object) -> MiscritInstance:
    defaults: dict[str, object] = dict(
        id="inst_001",
        template_id="fire_sprite",
        level=10,
        grade=Grade.B,
        stat_qualities=_all_qualities(),
        resolved_stats=_all_stats(),
    )
    defaults.update(overrides)
    return MiscritInstance(**defaults)  # type: ignore[arg-type]


class _FakeEffect:
    def __init__(self, id: str = "burn", name: str = "Burn", category: EffectCategory = EffectCategory.DOT, duration: int = 3) -> None:
        self.id = id
        self.name = name
        self.category = category
        self.duration = duration


# ── Creation ─────────────────────────────────────────────────────


class TestCreation:
    def test_hp_auto_initializes(self) -> None:
        inst = _make_instance()
        assert inst.current_hp == 120

    def test_max_hp(self) -> None:
        inst = _make_instance()
        assert inst.max_hp == 120

    def test_is_fainted_false(self) -> None:
        inst = _make_instance()
        assert inst.is_fainted is False

    def test_all_fields_accessible(self) -> None:
        inst = _make_instance()
        assert inst.id == "inst_001"
        assert inst.template_id == "fire_sprite"
        assert inst.level == 10
        assert inst.grade == Grade.B
        assert len(inst.stat_qualities) == 6
        assert len(inst.resolved_stats) == 6
        assert inst.active_effects == []


# ── HP behavior ──────────────────────────────────────────────────


class TestHP:
    def test_take_damage(self) -> None:
        inst = _make_instance()
        inst.current_hp -= 30
        assert inst.current_hp == 90

    def test_hp_clamped_at_zero(self) -> None:
        inst = _make_instance()
        inst.current_hp = -50
        assert inst.current_hp == 0

    def test_is_fainted_at_zero(self) -> None:
        inst = _make_instance()
        inst.current_hp = 0
        assert inst.is_fainted is True

    def test_hp_clamped_at_max(self) -> None:
        inst = _make_instance()
        inst.current_hp = 999
        assert inst.current_hp == 120

    def test_heal_does_not_exceed_max(self) -> None:
        inst = _make_instance()
        inst.current_hp = 100
        inst.current_hp += 50
        assert inst.current_hp == 120

    def test_damage_then_heal(self) -> None:
        inst = _make_instance()
        inst.current_hp -= 80
        assert inst.current_hp == 40
        inst.current_hp += 30
        assert inst.current_hp == 70


# ── Effect management ────────────────────────────────────────────


class TestEffects:
    def test_add_effect(self) -> None:
        inst = _make_instance()
        eff = _FakeEffect()
        inst.add_effect(eff)
        assert eff in inst.active_effects

    def test_remove_effect(self) -> None:
        inst = _make_instance()
        eff = _FakeEffect()
        inst.add_effect(eff)
        inst.remove_effect(eff)
        assert inst.active_effects == []

    def test_remove_missing_raises(self) -> None:
        inst = _make_instance()
        with pytest.raises(ValueError, match="not found"):
            inst.remove_effect(_FakeEffect())

    def test_tick_decrements_duration(self) -> None:
        inst = _make_instance()
        eff = _FakeEffect(duration=3)
        inst.add_effect(eff)
        inst.tick_effects()
        assert eff.duration == 2
        assert eff in inst.active_effects

    def test_tick_expires_at_zero(self) -> None:
        inst = _make_instance()
        eff = _FakeEffect(duration=1)
        inst.add_effect(eff)
        expired = inst.tick_effects()
        assert eff in expired
        assert eff not in inst.active_effects

    def test_tick_mixed_durations(self) -> None:
        inst = _make_instance()
        short = _FakeEffect(id="short", duration=1)
        long = _FakeEffect(id="long", duration=5)
        inst.add_effect(short)
        inst.add_effect(long)
        expired = inst.tick_effects()
        assert short in expired
        assert long not in expired
        assert long in inst.active_effects
        assert len(inst.active_effects) == 1

    def test_get_effects_by_category(self) -> None:
        inst = _make_instance()
        dot1 = _FakeEffect(id="burn", category=EffectCategory.DOT)
        dot2 = _FakeEffect(id="scorch", category=EffectCategory.DOT)
        buff = _FakeEffect(id="pa_up", category=EffectCategory.STAT_BUFF)
        inst.add_effect(dot1)
        inst.add_effect(dot2)
        inst.add_effect(buff)
        dots = inst.get_effects_by_category(EffectCategory.DOT)
        assert len(dots) == 2
        buffs = inst.get_effects_by_category(EffectCategory.STAT_BUFF)
        assert len(buffs) == 1

    def test_get_effects_by_category_empty(self) -> None:
        inst = _make_instance()
        assert inst.get_effects_by_category(EffectCategory.DOT) == []


# ── Validation ───────────────────────────────────────────────────


class TestValidation:
    def test_empty_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            _make_instance(id="")

    def test_whitespace_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            _make_instance(id="   ")

    def test_empty_template_id(self) -> None:
        with pytest.raises(ValueError, match="template_id cannot be empty"):
            _make_instance(template_id="")

    def test_level_zero(self) -> None:
        with pytest.raises(ValueError, match="Level must be 1-35"):
            _make_instance(level=0)

    def test_level_36(self) -> None:
        with pytest.raises(ValueError, match="Level must be 1-35"):
            _make_instance(level=36)

    def test_level_negative(self) -> None:
        with pytest.raises(ValueError, match="Level must be 1-35"):
            _make_instance(level=-1)

    def test_missing_resolved_stat(self) -> None:
        stats = _all_stats()
        del stats[Stat.HP]
        with pytest.raises(ValueError, match="resolved_stats must contain all 6 stats"):
            _make_instance(resolved_stats=stats)

    def test_zero_resolved_stat(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _make_instance(resolved_stats=_all_stats(hp=0))

    def test_negative_resolved_stat(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            _make_instance(resolved_stats=_all_stats(pa=-5))

    def test_missing_stat_quality(self) -> None:
        quals = _all_qualities()
        del quals[Stat.HP]
        with pytest.raises(ValueError, match="stat_qualities must contain all 6 stats"):
            _make_instance(stat_qualities=quals)

    def test_level_boundaries_valid(self) -> None:
        inst_1 = _make_instance(level=1)
        assert inst_1.level == 1
        inst_35 = _make_instance(level=35)
        assert inst_35.level == 35
