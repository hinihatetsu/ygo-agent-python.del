from .enums import CardLocation

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




