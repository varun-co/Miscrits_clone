from typing import Optional
from miscrits_clone.models.enums import Nature


class NatureResolver:
    def get_multiplier(
        self, attack_nature: Optional[Nature], defender_nature: list[Nature]
    ) -> float:

        if not defender_nature:
            raise ValueError("defender_nature must have at least 1 nature")

        if attack_nature is None:
            return 1.0

        if len(defender_nature) == 2 and not attack_nature.is_triangle_1:
            my_nature = defender_nature[1]
        else:
            my_nature = defender_nature[0]

        if attack_nature > my_nature:
            return 2.0
        elif attack_nature < my_nature:
            return 0.5
        return 1.0

    def is_strong(
        self, attack_nature: Optional[Nature], defender_nature: list[Nature]
    ) -> bool:
        return self.get_multiplier(attack_nature, defender_nature) == 2.0

    def is_weak(
        self, attack_nature: Optional[Nature], defender_nature: list[Nature]
    ) -> bool:
        return self.get_multiplier(attack_nature, defender_nature) == 0.5
