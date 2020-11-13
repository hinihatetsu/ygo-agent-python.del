from typing import Dict

from pyYGO.enums import CardLocation, CardPosition

class Location(int):
    """
    Location is logical sum of CardLocation
    """
    ZONE = CardLocation.MONSTER_ZONE | CardLocation.SPELL_ZONE
    @property
    def is_zone(self) -> bool:
        return bool(self & self.ZONE)

    @property
    def is_overlay(self) -> bool:
        return bool(self & CardLocation.OVERRAY)

    
    def __repr__(self) -> str:
        props = [repr(cl) for cl in CardLocation if self & cl]
        return ''.join(props)



class Position(int):
    pos_dict: Dict[int, CardPosition] = {int(pos): pos for pos in CardPosition}
    def __repr__(self) -> str:
        return self.pos_dict[self].__repr__()

