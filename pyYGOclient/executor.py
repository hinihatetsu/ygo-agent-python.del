from abc import ABC, abstractclassmethod
from typing import List, Tuple

from pyYGO import Card
from pyYGO.enums import Player
from pyYGO.phase import MainPhase, BattlePhase


class GameExecutor(ABC):
    @abstractclassmethod
    def on_start(self) -> None:
        """ Called when a new game starts. """
        pass


    @abstractclassmethod
    def on_new_turn(self) -> None:
        """ Called when a new turn starts. """
        pass


    @abstractclassmethod
    def on_new_phase(self) -> None:
        """ Called when a new phase starts. """
        pass


    @abstractclassmethod
    def on_win(self, win: bool) -> None:
        """ Called when a game ends. """
        pass

    
    @abstractclassmethod
    def on_rematch(self, win_on_match: bool) -> bool:
        """ Called when a match ends.\n
        Return True if you want to rematch. """
        pass


    @abstractclassmethod
    def select_tp(self) -> bool:
        """ Return True if you go first """
        pass

    @abstractclassmethod
    def select_mainphase_action(self, main: MainPhase) -> int:
        pass


    @abstractclassmethod
    def select_battle_action(self, battle: BattlePhase) -> int:
        pass


    @abstractclassmethod
    def select_effect_yn(self, card: Card, description: int) -> bool:
        pass


    @abstractclassmethod
    def select_yn(self) -> bool:
        pass


    @abstractclassmethod
    def select_battle_replay(self) -> bool:
        pass

    
    @abstractclassmethod
    def select_option(self, options: List[int]) -> int:
        pass


    @abstractclassmethod
    def select_card(self, choices: List[Card], min_: int, max_: int, cancelable: bool, select_hint: int) -> List[int]:
        pass

    
    @abstractclassmethod
    def select_tribute(self, choices: List[Card], min_: int, max_: int, cancelable: bool, select_hint: int) -> List[int]:
        pass
    

    @abstractclassmethod
    def select_chain(self, choices: List[Card], descriptions: List[int], forced: bool) -> int:
        pass


    @abstractclassmethod
    def select_place(self, player: Player, choices: List[int]) -> int:
        pass


    @abstractclassmethod
    def select_position(self, card_id: int, choices: List[int]) -> int:
        pass


    @abstractclassmethod
    def select_sum(self, choices: List[Tuple[Card, int, int]], sum_value: int, min_: int, max_: int, must_just: bool, select_hint: int) -> List[int]:
        pass


    @abstractclassmethod
    def select_unselect(self, choices: List[Card], min_: int, max_: int, cancelable: bool, hint: int):
        pass


    @abstractclassmethod
    def select_counter(self, counter_type: int, quantity: int, cards: List[Card], counters: List[int]) -> List[int]:
        pass


    @abstractclassmethod
    def select_number(self, choices: List[int]) -> int:
        pass


    @abstractclassmethod
    def sort_card(self, cards: List[Card]) -> List[int]:
        pass


    @abstractclassmethod
    def announce_attr(self, choices: List[int], count: int) -> List[int]:
        pass


    @abstractclassmethod
    def announce_race(self, choices: List[int], count: int) -> List[int]:
        pass


