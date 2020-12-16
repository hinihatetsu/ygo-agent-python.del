import random
import copy
from typing import NamedTuple

from pyYGO import Duel, Deck
from .action import Choice
from .flags import UsedFlag
from debug_tools import measure_time


class State(NamedTuple):
    duel: Duel
    usedflag: UsedFlag


class Decision(NamedTuple):
    selected: Choice
    choices: list[Choice]
    state: State

    def __repr__(self) -> str:
        return f'<Action:{repr(self.selected.action)}>'


class Memory(NamedTuple):
    decision: Decision
    next_state: State
    next_choices: list[Choice]
    reward: float


class ActionRecorder:
    THRESHOLD   = 500
    def __init__(self, deck: Deck) -> None:
        self._deck: Deck = deck
        self._decisions: list[Decision] = []
        self._memories: list[Memory] = []
        self._decision_cache: Decision = None

    
    def save(self, selected: Choice, choices: list[Choice], duel: Duel, usedflag: UsedFlag) -> None:
        state = State(copy.deepcopy(duel), copy.deepcopy(usedflag))
        self._decisions.append(Decision(selected, choices, state))


    def reward(self, reward: float) -> None:
        for i, dc in enumerate(reversed(self._decisions)):
            self._memories.append(Memory(dc, None,  None, reward))
        self._decisions.clear()


    def sample(self) -> list[Memory]:
        if len(self._memories) < self.THRESHOLD:
            return []
        sample = random.sample(self._memories, len(self._memories)-self.THRESHOLD//2)
        for mem in sample:
            self._memories.remove(mem)
        return sample

    
    def clear(self) -> None:
        self._memories.clear()


