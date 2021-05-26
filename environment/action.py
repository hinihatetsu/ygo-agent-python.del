import enum
from typing import NamedTuple


class Action(enum.IntEnum):
    SUMMON      = enum.auto()
    SP_SUMMON   = enum.auto()
    REPOSITION  = enum.auto()
    SET_MONSTER = enum.auto()
    SET_SPELL   = enum.auto()
    ACTIVATE    = enum.auto()
    BATTLE      = enum.auto()
    END         = enum.auto()

    ACTIVATE_IN_BATTLE = enum.auto()
    ATTACK             = enum.auto()
    MAIN2              = enum.auto()
    END_IN_BATTLE      = enum.auto()

    CHAIN  = enum.auto()
    SELECT = enum.auto()


class Choice(NamedTuple):
    action: Action
    index: int = 0
    card_id: int = 0
    option: int = 0

    
def Action_to_int(action: Action) -> int:
    convert = {
        Action.SUMMON:     0,
        Action.SP_SUMMON:  1,
        Action.REPOSITION: 2,
        Action.SET_MONSTER:3,
        Action.SET_SPELL:  4,
        Action.ACTIVATE:   5,
        Action.BATTLE:     6,
        Action.END:        7,

        Action.ACTIVATE_IN_BATTLE: 0,
        Action.ATTACK:             1,
        Action.MAIN2:              2,
        Action.END_IN_BATTLE:      3,

        Action.CHAIN:  20,
        Action.SELECT: 21
    }
    return convert[action]


