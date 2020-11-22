from typing import ValuesView

from pyYGOAgent.deck import Deck


class UsedFlag:
    def __init__(self, deck: Deck) -> None:
        self._flag: dict[int, bool] = dict()
        self.load(deck)


    @property
    def count(self) -> int:
        return len(self._flag)
        
    
    def load(self, deck: Deck) -> None:
        for card_id in deck.main + deck.extra:
            self._flag[card_id] = False


    def reset(self) -> None:
        for card_id in self._flag:
            self._flag[card_id] = False


    def used(self, card_id: int) -> None:
        self._flag[card_id] = True


    def values(self) -> ValuesView[bool]:
        return self._flag.values()


    
