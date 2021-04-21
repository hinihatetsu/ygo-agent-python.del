from typing import Union
from .enums import CardAttribute, CardLocation, CardPosition, CardRace, CardType

class Location:
    """ Location is logical sum of CardLocation """
    ZONE = CardLocation.MONSTER_ZONE | CardLocation.SPELL_ZONE
    def __init__(self, value: Union[int, CardLocation]) -> None:
        self._value: int = int(value)

    
    @property
    def value(self) -> int:
        return self._value


    def is_zone(self) -> bool:
        return bool(self._value & self.ZONE)


    def isa(self, loc: CardLocation) -> bool:
        """ Return True if it has CardLocation `loc`"""
        return bool(self._value & int(loc))


    def is_overlay(self) -> bool:
        return self.isa(CardLocation.OVERLAY)

    
    def __repr__(self) -> str:
        return ''.join(repr(loc) for loc in CardLocation if self.isa(loc))



class Type:
    def __init__(self, value: Union[int, CardType]) -> None:
        self._value: int = int(value)

    
    def isa(self, t: CardType) -> bool:
        """ Return True if it has CardType `t`."""
        return bool(self._value & int(t))


    def __repr__(self) -> str:
        return ''.join(repr(t) for t in CardType if self.isa(t))



class Attribute:
    def __init__(self, value: Union[int, CardAttribute]) -> None:
        self._value: int = int(value)


    def isa(self, attr: CardAttribute) -> bool:
        """ Return True if it has CardAttribute `attr`."""
        return bool(self._value & int(attr))


    def __repr__(self) -> str:
        return ''.join(repr(attr) for attr in CardAttribute if self.isa(attr))



class Race:
    def __init__(self, value: Union[int, CardRace]) -> None:
        self._value: int = int(value)


    def isa(self, race: CardRace) -> bool:
        """ Return True if it has CardRace `race`."""
        return bool(self._value & int(race))


    def __repr__(self) -> str:
        return ''.join(repr(race) for race in CardRace if self.isa(race))



class Position:
    def __init__(self, value: Union[int, CardPosition]) -> None:
        self._value: int = int(value)

    
    @property
    def value(self) -> int:
        return self._value

    
    def isa(self, pos: CardPosition) -> bool:
        return bool(self._value & int(pos))


    def is_attack(self) -> bool:
        return self.isa(CardPosition.ATTACK)


    def is_defence(self) -> bool:
        return self.isa(CardPosition.DEFENCE)


    def __repr__(self) -> str:
        return ''.join(repr(pos) for pos in CardPosition if self.isa(pos))
