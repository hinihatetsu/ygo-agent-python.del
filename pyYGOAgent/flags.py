from typing import Dict, ValuesView

from pyYGOAgent.deck import Deck


class UsedFlag:
    def __init__(self, deck: Deck) -> None:
        self.deck: Deck = deck
        self.flag: Dict[int, bool] = dict()
        self.load()


    @property
    def count(self) -> int:
        return len(self.flag)
        
    
    def load(self) -> None:
        for card_id in self.deck.main + self.deck.extra:
            self.flag[card_id] = False


    def reset(self) -> None:
        for card_id in self.flag:
            self.flag[card_id] = False


    def used(self, card_id: int) -> None:
        self.flag[card_id] = True


    def values(self) -> ValuesView[bool]:
        return self.flag.values()


    
