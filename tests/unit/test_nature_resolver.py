import pytest
from miscrits_clone.models.enums import Nature
from miscrits_clone.engine.nature_resolver import NatureResolver


@pytest.fixture
def resolver() -> NatureResolver:
    return NatureResolver()


# --- Triangle 1: Nature > Water > Fire > Nature ---

class TestTriangle1:
    def test_nature_beats_water(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.NATURE, [Nature.WATER]) == 2.0

    def test_water_beats_fire(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.WATER, [Nature.FIRE]) == 2.0

    def test_fire_beats_nature(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.FIRE, [Nature.NATURE]) == 2.0

    def test_water_weak_to_nature(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.WATER, [Nature.NATURE]) == 0.5

    def test_fire_weak_to_water(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.FIRE, [Nature.WATER]) == 0.5

    def test_nature_weak_to_fire(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.NATURE, [Nature.FIRE]) == 0.5


# --- Triangle 2: Wind > Earth > Lightning > Wind ---

class TestTriangle2:
    def test_wind_beats_earth(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.WIND, [Nature.EARTH]) == 2.0

    def test_earth_beats_lightning(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.EARTH, [Nature.LIGHTNING]) == 2.0

    def test_lightning_beats_wind(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.LIGHTNING, [Nature.WIND]) == 2.0

    def test_earth_weak_to_wind(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.EARTH, [Nature.WIND]) == 0.5

    def test_lightning_weak_to_earth(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.LIGHTNING, [Nature.EARTH]) == 0.5

    def test_wind_weak_to_lightning(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(Nature.WIND, [Nature.LIGHTNING]) == 0.5


# --- Cross-triangle (always neutral) ---

class TestCrossTriangle:
    @pytest.mark.parametrize("attacker,defender", [
        (Nature.FIRE, Nature.EARTH),
        (Nature.FIRE, Nature.LIGHTNING),
        (Nature.FIRE, Nature.WIND),
        (Nature.WATER, Nature.EARTH),
        (Nature.WATER, Nature.LIGHTNING),
        (Nature.WATER, Nature.WIND),
        (Nature.NATURE, Nature.EARTH),
        (Nature.NATURE, Nature.LIGHTNING),
        (Nature.NATURE, Nature.WIND),
        (Nature.EARTH, Nature.FIRE),
        (Nature.EARTH, Nature.WATER),
        (Nature.EARTH, Nature.NATURE),
        (Nature.LIGHTNING, Nature.FIRE),
        (Nature.LIGHTNING, Nature.WATER),
        (Nature.LIGHTNING, Nature.NATURE),
        (Nature.WIND, Nature.FIRE),
        (Nature.WIND, Nature.WATER),
        (Nature.WIND, Nature.NATURE),
    ])
    def test_cross_triangle_neutral(self, resolver: NatureResolver, attacker: Nature, defender: Nature) -> None:
        assert resolver.get_multiplier(attacker, [defender]) == 1.0


# --- Same nature (always neutral) ---

class TestSameNature:
    @pytest.mark.parametrize("nature", list(Nature))
    def test_same_nature_neutral(self, resolver: NatureResolver, nature: Nature) -> None:
        assert resolver.get_multiplier(nature, [nature]) == 1.0


# --- Physical attacks (null nature, always 1.0) ---

class TestPhysical:
    @pytest.mark.parametrize("defender", list(Nature))
    def test_physical_always_neutral(self, resolver: NatureResolver, defender: Nature) -> None:
        assert resolver.get_multiplier(None, [defender]) == 1.0

    def test_physical_vs_dual_nature(self, resolver: NatureResolver) -> None:
        assert resolver.get_multiplier(None, [Nature.FIRE, Nature.WIND]) == 1.0


# --- Dual-natured defenders ---

class TestDualNature:
    def test_fire_attack_vs_water_earth(self, resolver: NatureResolver) -> None:
        """Fire is weak to Water (same triangle). Earth is cross-triangle. Result: 0.5x"""
        assert resolver.get_multiplier(Nature.FIRE, [Nature.WATER, Nature.EARTH]) == 0.5

    def test_fire_attack_vs_nature_wind(self, resolver: NatureResolver) -> None:
        """Fire beats Nature (same triangle). Wind is cross-triangle. Result: 2.0x"""
        assert resolver.get_multiplier(Nature.FIRE, [Nature.NATURE, Nature.WIND]) == 2.0

    def test_fire_attack_vs_nature_earth(self, resolver: NatureResolver) -> None:
        """Fire beats Nature (same triangle). Earth is cross-triangle. Result: 2.0x"""
        assert resolver.get_multiplier(Nature.FIRE, [Nature.NATURE, Nature.EARTH]) == 2.0

    def test_wind_attack_vs_fire_earth(self, resolver: NatureResolver) -> None:
        """Wind beats Earth (same triangle). Fire is cross-triangle. Result: 2.0x"""
        assert resolver.get_multiplier(Nature.WIND, [Nature.FIRE, Nature.EARTH]) == 2.0

    def test_wind_attack_vs_water_lightning(self, resolver: NatureResolver) -> None:
        """Wind is weak to Lightning (same triangle). Water is cross-triangle. Result: 0.5x"""
        assert resolver.get_multiplier(Nature.WIND, [Nature.WATER, Nature.LIGHTNING]) == 0.5

    def test_fire_attack_vs_water_wind(self, resolver: NatureResolver) -> None:
        """Fire is weak to Water (same triangle). Wind is cross-triangle. Result: 0.5x"""
        assert resolver.get_multiplier(Nature.FIRE, [Nature.WATER, Nature.WIND]) == 0.5

    def test_cross_triangle_only_dual(self, resolver: NatureResolver) -> None:
        """Lightning vs (Fire + Earth): Fire is cross-triangle, Earth same triangle, Lightning beats nothing in T1.
        But Earth beats Lightning. Result: 0.5x"""
        assert resolver.get_multiplier(Nature.LIGHTNING, [Nature.FIRE, Nature.EARTH]) == 0.5

    def test_neutral_dual(self, resolver: NatureResolver) -> None:
        """Water vs (Fire + Wind): Water beats Fire (2.0x in same triangle). Wind is cross. Result: 2.0x"""
        assert resolver.get_multiplier(Nature.WATER, [Nature.FIRE, Nature.WIND]) == 2.0


# --- is_strong / is_weak helpers ---

class TestHelpers:
    def test_is_strong_true(self, resolver: NatureResolver) -> None:
        assert resolver.is_strong(Nature.FIRE, [Nature.NATURE]) is True

    def test_is_strong_false(self, resolver: NatureResolver) -> None:
        assert resolver.is_strong(Nature.FIRE, [Nature.WATER]) is False

    def test_is_weak_true(self, resolver: NatureResolver) -> None:
        assert resolver.is_weak(Nature.FIRE, [Nature.WATER]) is True

    def test_is_weak_false(self, resolver: NatureResolver) -> None:
        assert resolver.is_weak(Nature.FIRE, [Nature.NATURE]) is False

    def test_is_strong_physical(self, resolver: NatureResolver) -> None:
        assert resolver.is_strong(None, [Nature.FIRE]) is False

    def test_is_weak_physical(self, resolver: NatureResolver) -> None:
        assert resolver.is_weak(None, [Nature.FIRE]) is False


# --- Edge cases ---

class TestEdgeCases:
    def test_empty_defender_raises(self, resolver: NatureResolver) -> None:
        with pytest.raises(ValueError):
            resolver.get_multiplier(Nature.FIRE, [])

    def test_none_attack_empty_defender_raises(self, resolver: NatureResolver) -> None:
        with pytest.raises(ValueError):
            resolver.get_multiplier(None, [])
