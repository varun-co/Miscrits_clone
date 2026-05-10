import pytest
from miscrits_clone.models.enums import Nature, Rarity, Stat
from miscrits_clone.models.miscrit import Miscrit


VALID_STATS: dict[Stat, int] = {s: 3 for s in Stat}


def _make_miscrit(**overrides) -> Miscrit:
    defaults = dict(
        id="fire_sprite",
        name="Fire Sprite",
        natures=[Nature.FIRE],
        rarity=Rarity.COMMON,
        base_stats=VALID_STATS,
    )
    defaults.update(overrides)
    return Miscrit(**defaults)


# --- Valid construction ---


class TestValidCreation:
    def test_single_nature(self) -> None:
        m = _make_miscrit(natures=[Nature.FIRE])
        assert m.natures == [Nature.FIRE]

    def test_dual_nature_correct_order(self) -> None:
        m = _make_miscrit(natures=[Nature.FIRE, Nature.WIND])
        assert m.natures == [Nature.FIRE, Nature.WIND]

    def test_dual_nature_auto_sorted(self) -> None:
        m = _make_miscrit(natures=[Nature.WIND, Nature.FIRE])
        assert m.natures == [Nature.FIRE, Nature.WIND]

    def test_dual_nature_auto_sorted_all_combos(self) -> None:
        m = _make_miscrit(natures=[Nature.EARTH, Nature.WATER])
        assert m.natures == [Nature.WATER, Nature.EARTH]

        m = _make_miscrit(natures=[Nature.LIGHTNING, Nature.NATURE])
        assert m.natures == [Nature.NATURE, Nature.LIGHTNING]

    def test_all_fields_accessible(self) -> None:
        m = _make_miscrit(
            id="test_id",
            name="Test Name",
            natures=[Nature.WATER],
            rarity=Rarity.EPIC,
            base_stats={s: 5 for s in Stat},
            movelist=["tackle"],
        )
        assert m.id == "test_id"
        assert m.name == "Test Name"
        assert m.rarity == Rarity.EPIC
        assert m.base_stats[Stat.HP] == 5
        assert m.movelist == ["tackle"]

    def test_movelist_defaults_to_empty(self) -> None:
        m = _make_miscrit()
        assert m.movelist == []

    def test_base_stats_boundary_1(self) -> None:
        m = _make_miscrit(base_stats={s: 1 for s in Stat})
        assert m.base_stats[Stat.HP] == 1

    def test_base_stats_boundary_5(self) -> None:
        m = _make_miscrit(base_stats={s: 5 for s in Stat})
        assert m.base_stats[Stat.HP] == 5


# --- Invalid construction ---


class TestInvalidCreation:
    def test_empty_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            _make_miscrit(id="")

    def test_whitespace_id(self) -> None:
        with pytest.raises(ValueError, match="id cannot be empty"):
            _make_miscrit(id="   ")

    def test_empty_name(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            _make_miscrit(name="")

    def test_whitespace_name(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            _make_miscrit(name=" ")

    def test_empty_natures(self) -> None:
        with pytest.raises(ValueError, match="at least 1 nature"):
            _make_miscrit(natures=[])

    def test_three_natures(self) -> None:
        with pytest.raises(ValueError, match="more than 2 natures"):
            _make_miscrit(natures=[Nature.FIRE, Nature.WATER, Nature.WIND])

    def test_same_triangle_t1(self) -> None:
        with pytest.raises(ValueError, match="one nature from each triangle"):
            _make_miscrit(natures=[Nature.FIRE, Nature.WATER])

    def test_same_triangle_t2(self) -> None:
        with pytest.raises(ValueError, match="one nature from each triangle"):
            _make_miscrit(natures=[Nature.WIND, Nature.EARTH])

    def test_missing_base_stat(self) -> None:
        incomplete = {s: 3 for s in Stat if s != Stat.HP}
        with pytest.raises(ValueError, match="must contain all 6 stats"):
            _make_miscrit(base_stats=incomplete)

    def test_base_stat_too_low(self) -> None:
        bad = {s: 3 for s in Stat}
        bad[Stat.HP] = 0
        with pytest.raises(ValueError, match="must be between 1 and 5"):
            _make_miscrit(base_stats=bad)

    def test_base_stat_too_high(self) -> None:
        bad = {s: 3 for s in Stat}
        bad[Stat.EA] = 6
        with pytest.raises(ValueError, match="must be between 1 and 5"):
            _make_miscrit(base_stats=bad)

    def test_base_stat_negative(self) -> None:
        bad = {s: 3 for s in Stat}
        bad[Stat.SPD] = -1
        with pytest.raises(ValueError, match="must be between 1 and 5"):
            _make_miscrit(base_stats=bad)


# --- Movelist CRUD ---


class TestMovelistAdd:
    def test_add_attack(self) -> None:
        m = _make_miscrit()
        m.add_attack("fireball")
        assert m.movelist == ["fireball"]

    def test_add_multiple(self) -> None:
        m = _make_miscrit()
        m.add_attack("fireball")
        m.add_attack("tackle")
        assert m.movelist == ["fireball", "tackle"]

    def test_add_duplicate_rejected(self) -> None:
        m = _make_miscrit()
        m.add_attack("fireball")
        with pytest.raises(ValueError):
            m.add_attack("fireball")


class TestMovelistRemove:
    def test_remove_attack(self) -> None:
        m = _make_miscrit(movelist=["fireball", "tackle"])
        m.remove_attack("fireball")
        assert m.movelist == ["tackle"]

    def test_remove_last_attack(self) -> None:
        m = _make_miscrit(movelist=["fireball"])
        m.remove_attack("fireball")
        assert m.movelist == []

    def test_remove_missing_rejected(self) -> None:
        m = _make_miscrit()
        with pytest.raises(ValueError):
            m.remove_attack("fireball")


class TestMovelistReplace:
    def test_replace_attack(self) -> None:
        m = _make_miscrit(movelist=["fireball", "tackle"])
        m.replace_attack("fireball", "ember")
        assert m.movelist == ["ember", "tackle"]

    def test_replace_preserves_order(self) -> None:
        m = _make_miscrit(movelist=["a", "b", "c"])
        m.replace_attack("b", "x")
        assert m.movelist == ["a", "x", "c"]

    def test_replace_missing_old_rejected(self) -> None:
        m = _make_miscrit(movelist=["fireball"])
        with pytest.raises(ValueError):
            m.replace_attack("nonexistent", "ember")

    def test_replace_duplicate_new_rejected(self) -> None:
        m = _make_miscrit(movelist=["fireball", "tackle"])
        with pytest.raises(ValueError):
            m.replace_attack("fireball", "tackle")

    def test_replace_old_missing_and_new_exists(self) -> None:
        """When old is missing and new already exists, fail on old-not-found first."""
        m = _make_miscrit(movelist=["tackle"])
        with pytest.raises(ValueError, match="not found"):
            m.replace_attack("nonexistent", "tackle")


class TestMovelistHas:
    def test_has_attack_true(self) -> None:
        m = _make_miscrit(movelist=["fireball"])
        assert m.has_attack("fireball") is True

    def test_has_attack_false(self) -> None:
        m = _make_miscrit()
        assert m.has_attack("fireball") is False
