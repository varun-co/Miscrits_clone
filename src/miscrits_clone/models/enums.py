from enum import StrEnum

# --- Core Attributes ---


class Nature(StrEnum):
    NATURE = "NATURE"
    FIRE = "FIRE"
    WATER = "WATER"
    EARTH = "EARTH"
    LIGHTNING = "LIGHTNING"
    WIND = "WIND"


class Stat(StrEnum):
    HP = "HP"
    SPD = "SPD"
    PD = "PD"  # Physical Defense
    ED = "ED"  # Elemental Defense
    PA = "PA"  # Physical Attack
    EA = "EA"  # Elemental Attack


class Grade(StrEnum):
    F = "F"
    F_PLUS = "F_PLUS"
    E = "E"
    E_PLUS = "E_PLUS"
    D = "D"
    D_PLUS = "D_PLUS"
    C = "C"
    C_PLUS = "C_PLUS"
    B = "B"
    B_PLUS = "B_PLUS"
    A = "A"
    A_PLUS = "A_PLUS"
    S = "S"
    S_PLUS = "S_PLUS"


# --- Visuals & Classification ---


class StatQuality(StrEnum):
    RED = "RED"
    WHITE = "WHITE"
    GREEN = "GREEN"


class Rarity(StrEnum):
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"


# --- Combat Mechanics ---


class AttackType(StrEnum):
    PHYSICAL = "PHYSICAL"
    ELEMENTAL = "ELEMENTAL"


class EffectTrigger(StrEnum):
    ON_APPLY = "ON_APPLY"
    ON_TURN_START = "ON_TURN_START"
    ON_TURN_END = "ON_TURN_END"
    ON_HIT = "ON_HIT"
    ON_EXPIRE = "ON_EXPIRE"


class TargetRule(StrEnum):
    SELF = "SELF"
    SINGLE_OPPONENT = "SINGLE_OPPONENT"


class EffectCategory(StrEnum):
    STAT_BUFF = "STAT_BUFF"
    STAT_DEBUFF = "STAT_DEBUFF"
    DOT = "DOT"
    HOT = "HOT"
    FIXED_DOT = "FIXED_DOT"
    HEALING = "HEALING"
    DEFENSIVE = "DEFENSIVE"


# --- System & State Management ---


class BattleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class StackAction(StrEnum):
    APPLY_NEW = "APPLY_NEW"
    OVERWRITE = "OVERWRITE"
    REJECT = "REJECT"


TRIANGLE_1: set[Nature] = {Nature.NATURE, Nature.FIRE, Nature.WATER}
TRIANGLE_2: set[Nature] = {Nature.WIND, Nature.EARTH, Nature.LIGHTNING}


def get_triangle(nature: Nature) -> set[Nature]:
    return TRIANGLE_1 if nature in TRIANGLE_1 else TRIANGLE_2
