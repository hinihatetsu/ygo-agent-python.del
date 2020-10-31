from typing import NamedTuple, Dict

from pyYGO.enums import CardPosition, Player

class Location(int):
    """
    Location is logical sum of CardLocation
    """
    pass

class Position(int):
    pos_dict: Dict[int, CardPosition] = {int(pos): pos for pos in CardPosition}
    def __repr__(self) -> str:
        return self.pos_dict[self].__repr__()


class LocationInfo(NamedTuple):
    controller: Player
    location: Location
    idx: int
    position: Position