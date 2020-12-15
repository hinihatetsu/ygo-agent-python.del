from .card import Card

class MainPhase:
    def __init__(self):
        self.summonable: list[Card] = []
        self.special_summonable: list[Card] = []
        self.repositionable: list[Card] = []
        self.moster_settable: list[Card] = []
        self.spell_settable: list[Card] = []
        self.activatable: list[Card] = []
        self.activation_descs: list[int] = []

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
        self.attackable: list[Card] = []
        self.activatable: list[Card] = []
        self.activation_descs: list[int] = []

        self.can_main2: bool = None
        self.can_end: bool = None


        