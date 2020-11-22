import math
import datetime
import csv
from pathlib import Path
from typing import Any, NamedTuple

from pyYGO.duel import Duel
from pyYGO.enums import Player
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action
from pyYGOAgent.flags import UsedFlag


class Decision(NamedTuple):
    action: Action
    card_id: int
    option: Any
    duel: Duel
    usedflag: UsedFlag
    value: float

    def __repr__(self) -> str:
        return f'<Action:{repr(self.action)}; value:{self.value}>'



class DecisionRecorder:
    DISCOUNT_RATE = 0.8
    def __init__(self, deck: Deck) -> None:
        self._deck: Deck = deck
        self._decisions: list[Decision] = []
        self._evaluated_decisions: list[Decision] = []
        self._hand_cache: list[int] = None
        self._field_cache: list[int] = None
        self._deck_cache: list[int] = None
        self._life_cache: list[int] = None
        self._match_result: list[bool] = []

    
    def save(self, decision: Decision) -> None:
        self._decisions.append(decision)


    def load(self) -> list[Decision]:
        return self._evaluated_decisions

    
    def clear(self) -> None:
        self._evaluated_decisions.clear()


    def calculate_reward(self, duel: Duel) -> None:
        score: list[float] = [0, 0]
        for p in (Player.ME, Player.OPPONENT):
            hand = (duel.field[p].hand_count - self._hand_cache[p]) / 2
            field = (duel.field[p].field_count - self._field_cache[p]) 
            deck = (self._deck_cache[p] - duel.field[p].deck_count) / 8
            life = (self._life_cache[p^1] - duel.life[p^1]) / 1000
            score[p] = 1 / (1 + math.exp(-(hand + field + deck + life))) # sigmoid
            self._deck_cache[p] = duel.field[p].deck_count
            self._life_cache[p^1] = duel.life[p^1]
        reward: float = score[Player.ME] - score[Player.OPPONENT]

        for i, dc in enumerate(reversed(self._decisions)):
            dc = Decision(dc.action, dc.card_id, dc.option, dc.duel, dc.usedflag, dc.value + reward * self.DISCOUNT_RATE**i)
            self._evaluated_decisions.append(dc)
        
        self._decisions.clear()


    def reset_cache(self) -> None:
        self._hand_cache = [5, 5]
        self._field_cache = [0, 0]
        self._deck_cache = [35, 35]
        self._life_cache = [8000, 8000]


    def save_match_result(self, match_count: int, win: bool):
        size = len(self._match_result)
        if size >= match_count:
            self._match_result = self._match_result[:match_count]
        for _ in range(match_count - size - 1):
            self._match_result.append(None)
        self._match_result.append(win)


    def dump_match_result(self) -> None:
        now = datetime.datetime.now().isoformat(timespec='seconds').replace(':', '-')
        file = Path.cwd() / 'Decks' / self._deck.name / (now + '.csv')
        with file.open(mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow('match', 'win')
            writer.writerows(enumerate(self._match_result))
        self._match_result.clear()

