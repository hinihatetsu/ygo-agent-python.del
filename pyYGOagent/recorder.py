import random
import pickle
from typing import NamedTuple

from pyYGO import Duel
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


class PickledMemory(NamedTuple):
    decision_bytes: bytes
    next_state_bytes: bytes
    next_choices_bytes: bytes
    reward: float


class Memory(NamedTuple):
    decision: Decision
    next_state: State
    next_choices: list[Choice]
    reward: float


class ActionRecorder:
    THRESHOLD   = 500
    def __init__(self) -> None:
        self._decisions: list[bytes] = []
        self._memories: list[PickledMemory] = []
        self._decision_cache: Decision = None

    
    def save(self, selected: Choice, choices: list[Choice], duel: Duel, usedflag: UsedFlag) -> None:
        state = State(duel, usedflag)
        self._decisions.append(pickle.dumps(Decision(selected, choices, state)))


    def reward(self, reward: float) -> None:
        for i, dc in enumerate(reversed(self._decisions)):
            self._memories.append(PickledMemory(dc, pickle.dumps(None), pickle.dumps(None), reward))
        self._decisions.clear()


    def sample(self) -> list[Memory]:
        if len(self._memories) < self.THRESHOLD:
            return []
        sample = random.sample(self._memories, len(self._memories)-self.THRESHOLD//2)
        for mem in sample:
            self._memories.remove(mem)
        return [Memory(pickle.loads(mem.decision_bytes), pickle.loads(mem.next_state_bytes), pickle.loads(mem.next_choices_bytes), mem.reward) for mem in sample]

    
    def clear(self) -> None:
        self._memories.clear()


