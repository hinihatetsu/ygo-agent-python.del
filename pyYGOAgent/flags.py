from typing import Dict

from pyYGOAgent.deck import Deck


class UsedFlag(Dict[int, bool]):
    def __init__(self, deck: Deck) -> None:
        self.deck: Deck = deck
        self.load()


    @property
    def count(self) -> int:
        return len(self)
        
    
    def load(self) -> None:
        for card_id in self.deck.main + self.deck.extra:
            self[card_id] = False


    def reset(self) -> None:
        for card_id in self:
            self[card_id] = False


    def used(self, card_id: int) -> None:
        self[card_id] = True


    
