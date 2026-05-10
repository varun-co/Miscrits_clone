import pytest
from miscrits_clone.models.enums import AttackType, Nature, TargetRule
from miscrits_clone.models.attack import Attack


def _make_attack(**overrides) -> Attack:
    defaults = dict(
        id="fireball",
        name="Fireball",
        description="A blazing ball of fire.",
        type=AttackType.ELEMENTAL,
        nature=Nature.FIRE,
        power=45,
        accuracy=90,
    )
    defaults.update(overrides)
    return Attack(**defaults)


def _make_physical(**overrides) -> Attack:
    defaults = dict(
        id="tackle",
        name="Tackle",
        description="A basic physical strike.",
        type=AttackType.PHYSICAL,
        nature=None,
        power=30,
        accuracy=95,
    )
    defaults.update(overrides)
    return Attack(**defaults)


# --- Valid construction ---


class TestValidCreation:
    def test_elemental_attack(self) -> None:
        a = _make_attack()
        assert a.id == "fireball"
        assert a.name == "Fireball"
        assert a.description == "A blazing ball of fire."
        assert a.type == AttackType.ELEMENTAL
        assert a.nature == Nature.FIRE
        assert a.power == 45
        assert a.accuracy == 90

    def test_physical_attack(self) -> None:
        a = _make_physical()
        assert a.type == AttackType.PHYSICAL
        assert a.nature is None

    def test_default_effect_ids_empty(self) -> None:
        a = _make_attack()
        assert a.effect_ids == []

    def test_default_target_rule(self) -> None:
        a = _make_attack()
        assert a.target_rule == TargetRule.SINGLE_OPPONENT

    def test_explicit_effect_ids(self) -> None:
        a = _make_attack(effect_ids=["burn", "stat_debuff"])
        assert a.effect_ids == ["burn", "stat_debuff"]

    def test_explicit_target_rule_self(self) -> None:
        a = _make_attack(target_rule=TargetRule.SELF)
        assert a.target_rule == TargetRule.SELF

    def test_accuracy_boundary_0(self) -> None:
        a = _make_attack(accuracy=0)
        assert a.accuracy == 0

    def test_accuracy_boundary_100(self) -> None:
        a = _make_attack(accuracy=100)
        assert a.accuracy == 100

    def test_power_boundary_1(self) -> None:
        a = _make_attack(power=1)
        assert a.power == 1

    def test_all_natures_valid_for_elemental(self) -> None:
        for nature in Nature:
            a = _make_attack(nature=nature)
            assert a.nature == nature


# --- Immutability ---


class TestFrozen:
    def test_cannot_assign_power(self) -> None:
        a = _make_attack()
        with pytest.raises(AttributeError):
            a.power = 10  # type: ignore[misc]

    def test_cannot_assign_accuracy(self) -> None:
        a = _make_attack()
        with pytest.raises(AttributeError):
            a.accuracy = 50  # type: ignore[misc]

    def test_cannot_assign_name(self) -> None:
        a = _make_attack()
        with pytest.raises(AttributeError):
            a.name = "New Name"  # type: ignore[misc]


# --- Invalid construction ---


class TestInvalidCreation:
    def test_elemental_with_null_nature(self) -> None:
        with pytest.raises(ValueError, match="Elemental attack must have a nature"):
            _make_attack(nature=None)

    def test_physical_with_nature(self) -> None:
        with pytest.raises(ValueError, match="Physical attack must not have a nature"):
            _make_physical(nature=Nature.FIRE)

    def test_power_zero(self) -> None:
        with pytest.raises(ValueError, match="power must be positive"):
            _make_attack(power=0)

    def test_power_negative(self) -> None:
        with pytest.raises(ValueError, match="power must be positive"):
            _make_attack(power=-5)

    def test_accuracy_below_zero(self) -> None:
        with pytest.raises(ValueError, match="accuracy must be 0-100"):
            _make_attack(accuracy=-1)

    def test_accuracy_above_100(self) -> None:
        with pytest.raises(ValueError, match="accuracy must be 0-100"):
            _make_attack(accuracy=150)

    def test_empty_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            _make_attack(id="")

    def test_whitespace_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            _make_attack(id="   ")

    def test_empty_name(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            _make_attack(name="")

    def test_whitespace_name(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            _make_attack(name=" ")
