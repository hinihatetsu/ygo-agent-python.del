import math
import copy
import datetime
import pickle
from pathlib import Path
from typing import Any, NamedTuple

from pyYGO.duel import Duel
from pyYGO.enums import Player
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action
from pyYGOAgent.flags import UsedFlag


class Dicision(NamedTuple):
    action: Action
    card_id: int
    duel: Duel
    usedflag: UsedFlag
    option: Any = None
    value: float = 0

    def __repr__(self) -> str:
        return f'Action:{self.action}; value:{self.value}'



class DicisionRecorder:
    DISCOUNT_RATE = 0.6
    def __init__(self, deck: Deck, duel: Duel, usedflag: UsedFlag) -> None:
        self.deck: Deck = deck
        self.duel: Duel = duel
        self.usedflag: UsedFlag = usedflag

        self.dicisions: list[Dicision] = []
        self.evaluated_dicisions: list[Dicision] = []
        self.hand_cache: list[int] = None
        self.field_cache: list[int] = None
        self.deck_cache: list[int] = None
        self.life_cache: list[int] = None

        self.record_dir: Path = Path.cwd() / 'Decks' / self.deck.name / 'Records'
        if not self.record_dir.exists():
            self.record_dir.mkdir()

    
    def save_dicision(self, action: Action, card_id: int, option: Any) -> None:
        dc = Dicision(action, card_id, copy.deepcopy(self.duel), copy.deepcopy(self.usedflag), option)
        self.dicisions.append(dc)


    def evaluate(self) -> None:
        scores: list[float] = [0, 0]
        for p in (Player.ME, Player.OPPONENT):
            hand = (self.duel.field[p].hand_count - self.hand_cache[p]) / 2
            field = (self.duel.field[p].field_count - self.field_cache[p]) 
            deck = (self.deck_cache[p] - self.duel.field[p].deck_count) / 8
            life = (self.life_cache[p^1] - self.duel.life[p^1]) / 1000
            scores[p] = 1 / (1 + math.exp(-(hand + field + deck + life))) # sigmoid
            self.deck_cache[p] = self.duel.field[p].deck_count
            self.life_cache[p^1] = self.duel.life[p^1]
        score: float = scores[Player.ME] - scores[Player.OPPONENT]

        for i, dc in enumerate(reversed(self.dicisions)):
            dc = Dicision(dc.action, dc.card_id, dc.duel, dc.usedflag, dc.option, score * self.DISCOUNT_RATE**i)
            self.evaluated_dicisions.append(dc)
        
        self.dicisions.clear()
        self.dump()


    def dump(self) -> None:
        now = datetime.datetime.now()
        for index, dc in enumerate(self.evaluated_dicisions):
            save_path = self.record_dir / (now.isoformat(sep='-', timespec='seconds').replace(':', '-') + f'_{index}.dicision')
            with open(save_path, mode='wb') as f:
                pickle.dump(dc, f)

        self.evaluated_dicisions.clear()


    def reset_cache(self) -> None:
        self.hand_cache: list[int] = [5, 5]
        self.field_cache: list[int] = [0, 0]
        self.deck_cache: list[int] = [35, 35]
        self.life_cache: list[int] = [8000, 8000]