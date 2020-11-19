from typing import ValuesView, NoReturn

from pyYGOAgent.deck import Deck


class UsedFlag:
    def __init__(self, deck: Deck) -> NoReturn:
        self.deck: Deck = deck
        self.flag: dict[int, bool] = dict()
        self.load()


    @property
    def count(self) -> int:
        return len(self.flag)
        
    
    def load(self) -> NoReturn:
        for card_id in self.deck.main + self.deck.extra:
            self.flag[card_id] = False


    def reset(self) -> NoReturn:
        for card_id in self.flag:
            self.flag[card_id] = False


    def used(self, card_id: int) -> NoReturn:
        self.flag[card_id] = True


    def values(self) -> ValuesView[bool]:
        return self.flag.values()


    
