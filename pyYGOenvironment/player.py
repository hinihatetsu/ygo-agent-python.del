from abc import ABC, abstractclassmethod
from pyYGO.enums import Player

from pyYGO import Card, Deck, Location
from pyYGO.enums import Player, CardPosition, Attribute, Race
from pyYGO.phase import MainPhase, BattlePhase


class GamePlayer(ABC):
    @abstractclassmethod
    def on_start(self) -> None:
        """ Called when a game starts. """
        pass


    @abstractclassmethod
    def on_new_turn(self, is_my_turn: bool) -> None:
        """ Called when a new turn starts. """
        pass


    @abstractclassmethod
    def on_win(self, win: bool) -> None:
        """ Called when a game ends. """
        pass

    
    @abstractclassmethod
    def on_rematch(self) -> bool:
        """ Called when a match ends.\n
        Return True if you want to rematch. """
        pass


    @abstractclassmethod
    def on_client_close(self) -> None:
        """ Called when the client close """
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
    def select_option(self, options: list[int]) -> int:
        pass


    @abstractclassmethod
    def select_card(self, choices: list[int], max_: int, cancelable: bool, select_hint: int) -> list[int]:
        pass


    @abstractclassmethod
    def select_chain(self, choices: list[Card], descriptions: list[int], forced: bool) -> int:
        pass


    @abstractclassmethod
    def select_place(self, player: Player, location: Location, selectable: int, is_pzone: bool) -> int:
        pass


    @abstractclassmethod
    def select_position(self, card_id: int, choices: list[CardPosition]) -> int:
        pass


    @abstractclassmethod
    def select_sum(self, choices: list[Card], min_: int, max_: int, cancelable: bool, select_hint: int):
        pass


    @abstractclassmethod
    def select_unselect(self, choices: list[Card], min_: int, max_: int, cancelable: bool, hint: int):
        pass


    @abstractclassmethod
    def select_counter(self, counter_type: int, quantity: int, cards: list[int], counters: list[int]) -> list[int]:
        pass


    @abstractclassmethod
    def select_number(self, choices: list[int]) -> int:
        pass


    @abstractclassmethod
    def sort_card(self, cards: list[Card]) -> list[int]:
        pass


    @abstractclassmethod
    def announce_attr(self, choices: list[Attribute], count: int) -> list[int]:
        pass


    @abstractclassmethod
    def announce_race(self, choices: list[Race], count: int) -> list[int]:
        pass


