import math
import copy
import datetime
import pickle
from pathlib import Path
from typing import Any, List, NamedTuple

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
    value: float = 0
    option: Any = None



class DicisionRecorder:
    def __init__(self, deck: Deck, duel: Duel, usedflag: UsedFlag) -> None:
        self.deck: Deck = deck
        self.duel: Duel = duel
        self.usedflag: UsedFlag = usedflag

        self.dicisions: List[Dicision] = []
        self.evaluated_dicisions: List[Dicision] = []
        self.hand_cache: List[int] = [5, 5]
        self.field_cache: List[int] = [0, 0]
        self.deck_cache: List[int] = [35, 35]
        self.life_cache: List[int] = [8000, 8000]

        self.record_dir: Path = Path.cwd() / 'Decks' / self.deck.name / 'Records'
        if not self.record_dir.exists():
            self.record_dir.mkdir()

    
    def save_dicision(self, action: Action, card_id: int, option: Any) -> None:
        self.dicisions.append(Dicision(action, card_id, copy.deepcopy(self.duel), copy.deepcopy(self.usedflag), option=option))


    def evaluate(self) -> None:
        scores: List[float] = [0, 0]
        for p in (Player.ME, Player.OPPONENT):
            hand = (self.duel.field[p].hand_count - self.hand_cache[p]) 
            field = (self.duel.field[p].field_count - self.field_cache[p]) / 2
            deck = (self.deck_cache[p] - self.duel.field[p].deck_count) / 4
            life = (self.life_cache[p^1] - self.duel.field[p^1].life) / 2000
            scores[p] = 1 / (1 + math.exp(-(hand + field + deck + life))) # sigmoid
            self.deck_cache[p] = self.duel.field[p].deck_count
            self.life_cache[p^1] = self.duel.field[p^1].life
        score: float = scores[Player.ME] - scores[Player.OPPONENT]

        for dc in self.dicisions:
            self.evaluated_dicisions.append(Dicision(dc.action, dc.card_id, dc.duel, dc.usedflag, score, dc.option))
        
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
        self.hand_cache: List[int] = [5, 5]
        self.field_cache: List[int] = [0, 0]
        self.deck_cache: List[int] = [35, 35]
        self.life_cache: List[int] = [8000, 8000]