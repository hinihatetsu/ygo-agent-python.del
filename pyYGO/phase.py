from typing import List

from pyYGO.card import Card

class MainPhase:
    def __init__(self):
        self.summonable: List[Card] = []
        self.special_summonable: List[Card] = []
        self.repositionable: List[Card] = []
        self.moster_settable: List[Card] = []
        self.spell_settable: List[Card] = []
        self.activatable: List[Card] = []
        self.activation_descs: List[Card] = []

        self.can_battle: bool = None
        self.can_end: bool = None


    def __iter__(self):
        return self.__generator__()


    def __generator__(self):
        yield self.summonable
        yield self.special_summonable
        yield self.repositionable
        yield self.moster_settable
        yield self.spell_settable
        yield self.activatable


    def __len__(self) -> int:
        return sum(len(lst) for lst in self)


class BattlePhase:
    def __init__(self) -> None:
        self.attackable: List[Card] = []
        self.activatable: List[Card] = []
        self.activation_descs: List[int] = []

        self.can_main2: bool = None
        self.can_end: bool = None


        