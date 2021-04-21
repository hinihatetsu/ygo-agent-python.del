import random
from threading import Lock, Event
from typing import List, Tuple

import numpy as np

from .action import Choice, Action, Action_to_int
from .flags import UsedFlag
from .preprocess import create_state
from pyYGO import Deck, Duel, Card
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import Player
from pyYGOclient import GameExecutor, GameClient

timeout = 10


class EnvGameExecutor(GameExecutor):
    def __init__(self, client: GameClient) -> None:
        self._client: GameClient = client
        client.set_executor(self)
        self._duel: Duel = client.get_duel()
        self._deck: Deck = client.get_deck()
        self._deck_list: List[int] = self._deck.main + self._deck.extra
        self._usedflag: UsedFlag = UsedFlag(self._deck)

        self._state: np.ndarray = create_state(Action.END, 0, 0, self._duel, self._usedflag, self._deck_list)
        self.state_shape = self._state.shape
        self._should_execute: bool = False
        self._state_has_updated: Event = Event()
        self._should_execute_has_updated: Event = Event()

        self._reward: float = 0.0
        self._reward_lock: Lock = Lock()
        self._game_ended: Event = Event()
        self._rematch: Event = Event()
        self._rematch.set()


    def run(self) -> None:
        self._client.start()

    
    def close(self) -> None:
        self._rematch.clear()
        self._should_execute_has_updated.set()
        self._state_has_updated.set()


    def get_state(self) -> np.ndarray:
        self._state_has_updated.wait(timeout)
        state = self._state
        self._state_has_updated.clear()
        return state


    def execute(self, should_execute: bool) -> None:
        self._should_execute = should_execute
        self._should_execute_has_updated.set()


    def game_ended(self) -> bool:
        return self._game_ended.is_set()


    def get_reward(self) -> float:
        with self._reward_lock:
            reward = self._reward
        return reward
    
    
    def _select(self, choices: List[Choice]) -> Choice:
        if not self._rematch.is_set():
            self._client.surrender()
        
        for choice in choices:
            self._state = create_state(choice.action, choice.card_id, choice.option, self._duel, self._usedflag, self._deck_list)
            self._state_has_updated.set()
            self._should_execute_has_updated.clear()
            self._should_execute_has_updated.wait(timeout)
            if self._should_execute:
                return choice
        return choices[-1]

    
    def on_start(self) -> None:
        with self._reward_lock:
            self._reward = 0.0
        self._game_ended.clear()

    
    def on_new_turn(self) -> None:
        self._usedflag.reset()
    

    def on_new_phase(self) -> None:
        pass


    def on_win(self, win: bool) -> None:
        with self._reward_lock:
            self._reward = 100.0 if win else 0.0
        self._game_ended.set()
        self._state_has_updated.set()

        
    
    def on_rematch(self, win_on_match: bool) -> bool:
        return self._rematch.is_set()
  
    
    def _update_usedflag(self, card_id: int) -> None:
        self._usedflag.used(card_id)


    def select_tp(self) -> bool:
        return True
        

    def select_mainphase_action(self, main: MainPhase) -> int:
        choices: List[Choice] = []

        for index, card in enumerate(main.summonable):
            choices.append(Choice(Action.SUMMON, index, card.id))
        
        for index, card in enumerate(main.special_summonable):
            choices.append(Choice(Action.SP_SUMMON, index, card.id))

        for index, card in enumerate(main.repositionable):
            choices.append(Choice(Action.REPOSITION, index, card.id))

        for index, card in enumerate(main.monster_settable):
            choices.append(Choice(Action.SET_MONSTER, index, card.id))

        for index, card in enumerate(main.spell_settable):
            choices.append(Choice(Action.SET_SPELL, index, card.id))

        for index, card in enumerate(main.activatable):
            desc: int = main.activation_descs[index]
            choices.append(Choice(Action.ACTIVATE, index, card.id, desc))

        if main.can_battle:
            choices.append(Choice(Action.BATTLE))

        if main.can_end:
            choices.append(Choice(Action.END))

        selected: Choice = self._select(choices)    
        if selected.action is Action.ACTIVATE:
            self._update_usedflag(selected.card_id)

        return (selected.index << 16) + Action_to_int(selected.action)


    def select_battle_action(self, battle: BattlePhase) -> int:
        choices: List[Choice] = []

        for index, card in enumerate(battle.attackable):
            choices.append(Choice(Action.ATTACK, index, card.id))

        for index, card in enumerate(battle.activatable):
            desc: int = battle.activation_descs[index]
            choices.append(Choice(Action.ACTIVATE_IN_BATTLE, index, card.id, option=desc))

        if battle.can_main2:
            choices.append(Choice(Action.MAIN2))

        selected: Choice = self._select(choices)
        if selected.action == Action.ACTIVATE_IN_BATTLE:
            self._update_usedflag(selected.card_id)

        return (selected.index << 16) + Action_to_int(selected.action)


    def select_effect_yn(self, card: Card, desc: int) -> bool:
        return True


    def select_yn(self) -> bool:
        return True


    def select_battle_replay(self) -> bool:
        return True

    
    def select_option(self, options: List[int]) -> int:
        return random.choice(list(range(len(options))))


    def select_card(self, cards: List[Card], min_: int, max_: int, cancelable: bool, hint: int) -> List[int]:
        choices: List[Choice] = []
        for index, card in enumerate(cards):
            choices.append(Choice(Action.SELECT, index, card.id, option=hint))

        num_to_select: int = max_ # ToDo: more intelligent
        selecteds: List[Choice] = []
        for _ in range(max_):
            selected: Choice = self._select(choices)
            selecteds.append(selected)
            choices.remove(selected)
        return [selected.index for selected in selecteds]


    def select_chain(self, cards: List[Card], descriptions: List[int], forced: bool) -> int:
        choices: List[Choice] = []

        for index, card in enumerate(cards):
            desc = descriptions[index]
            choices.append(Choice(Action.CHAIN, index, card.id, desc))

        if not forced:
            choices.append(Choice(Action.CHAIN, -1, card_id=0, option=0)) # -1 means no activation

        selected: Choice = self._select(choices)
        if selected.index != -1:
            self._update_usedflag(selected.card_id)

        return selected.index


    def select_place(self, player: Player, choices: List[int]) -> int:
        ans: int = random.choice(choices)

        return ans 


    def select_position(self, card_id: int, choices: List[int]) -> int:
        return choices[0]


    def select_tribute(self, choices: List[Card], min_: int, max_: int, cancelable: bool, hint: int) -> List[int]:
        my_card: List[Card] = sorted([card for card in choices if card.controller == Player.ME], key=lambda x:x.attack)
        op_card: List[Card] = sorted([card for card in choices if card.controller == Player.OPPONENT], key=lambda x:-x.attack)
        choosed: List[Card] = (op_card + my_card)[0:max_]
        return [choices.index(card) for card in choosed]
    

    def select_sum(self, choices: List[Tuple[Card, int, int]], sum_value: int, min_: int, max_: int, must_just: bool, select_hint: int) -> List[int]:
        raise Exception('not complete coding')


    def select_unselect(self, choices: List[Card], min_: int, max_: int, cancelable: bool, hint: int):
        return self.select_card(choices, min_, max_, cancelable, hint)


    def select_counter(self, counter_type: int, quantity: int, cards: List[Card], counters: List[int]) -> List[int]:
        raise Exception('not complete coding')


    def select_number(self, choices: List[int]) -> int:
        raise Exception('not complete coding')

    
    def sort_card(self, cards: List[Card]) -> List[int]:
        raise Exception('not complete coding')


    def announce_attr(self, choices: List[int], count: int) -> List[int]:
        raise Exception('not complete coding')


    def announce_race(self, choices: List[int], count: int) -> List[int]:
        raise Exception('not complete coding')



