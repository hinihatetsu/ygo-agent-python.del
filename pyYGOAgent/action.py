import enum
from typing import NamedTuple, Any


class Action(enum.IntEnum):
    SUMMON = 0
    SP_SUMMON = 1
    REPOSITION = 2
    SET_MONSTER = 3
    SET_SPELL = 4
    ACTIVATE = 5
    BATTLE = 6
    END = 7

    ACTIVATE_IN_BATTLE = 10
    ATTACK = 11
    MAIN2 = 12
    END_IN_BATTLE = 13

    CHAIN = 20
    SELECT = 21



class MainAction(NamedTuple):
    value: float
    action: Action
    index: int = 0
    card_id: int = None
    option: Any = None

    def to_int(self) -> int:
        return (self.index << 16) + int(self.action)



class BattleAction(NamedTuple):
    value: float
    action: Action
    index: int = 0
    card_id: int = None
    option: Any = None

    def to_int(self) -> int:
        return (self.index << 16) + int(self.action - 10)



class ChainAction(NamedTuple):
    value: float
    index: int
    card_id: int
    desc: int
    action: Action = Action.CHAIN

    def to_int(self) -> int:
        return self.index



class SelectAction(NamedTuple):
    value: float
    index: int
    card_id: int
    hint: int
    action: Action = Action.SELECT
