import enum
from typing import Any, NamedTuple


class Action(enum.Enum):
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
    option: Any = None


class EvaluatedChoice(NamedTuple):
    choice: Choice
    value: float

    
   


