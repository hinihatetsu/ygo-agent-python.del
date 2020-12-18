import random
import datetime
import csv
import math
import copy
from pathlib import Path

from pyYGO import Duel, Card, Zone, Deck, Location
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import CardPosition, Player, Attribute, Race
from pyYGOenvironment import GameClient, GamePlayer
from .action import Action, Choice
from .brain import AgentBrain
from .flags import UsedFlag



class DuelAgent(GamePlayer):
    _MAX_MATCH: int = 1000
    def __init__(self, deck_name: str, no_train: bool=True) -> None:
        self._deck: Deck = Deck(deck_name)
        self._brain: AgentBrain = AgentBrain(self._deck)
        self._usedflag: UsedFlag = UsedFlag(self._deck)
        self._no_train: bool = no_train

        self._duel: Duel = None
        self._duel_cache: Duel = None
        self._match_count: int = 0
        self._wins: int = 0
        self._match_result: list[bool] = []

        

    def set_client(self, client: GameClient) -> None:
        """ set client where agent play """
        self._client = client
        client.set_gameplayer(self)
        self._duel = client.get_duel()


    def run(self):
        """ agent starts to run """
        if self._client is None:
            raise Exception('GameClient not set. Call DuelAgent.set_client().')
        self._client.set_deck(self._deck)
        self._client.start()

    
    def on_start(self) -> None:
        self._duel_cache = None

    
    def on_new_turn(self) -> None:
        self._usedflag.reset()
        if self._duel.turn_player == Player.ME:
            reward = self._calculate_reward()
            self._brain.feedback(reward)
    

    def on_new_phase(self) -> None:
        pass


    def on_win(self, win: bool) -> None:
        reward = self._calculate_reward()
        self._brain.feedback(reward)
        
    
    def on_rematch(self, win_on_match: bool) -> bool:
        self._match_count += 1
        self._wins += 1 if win_on_match else 0
        self._match_result.append(win_on_match)
        assert len(self._match_result) == self._match_count, "len(self._match_result) != match_count"
        
        self._print_match_result(win_on_match)
        if self._no_train:
            self._brain.clear_memory()
        else:
            self._brain.train()
        return True if self._match_count < self._MAX_MATCH else False


    def on_close(self) -> None:
        self._dump_match_result()
        if not self._no_train:
            self._brain.save_networks()

    
    def _calculate_reward(self) -> float:
        if self._duel_cache is None:
            self._duel_cache = self._duel

        score: list[float] = [0, 0]
        for p in (Player.ME, Player.OPPONENT):
            field = (self._duel.field[p].field_count - self._duel_cache.field[p].field_count) 
            life = -(self._duel.life[p^1] - self._duel_cache.life[p^1]) / 1000

            score[p] = 1 / (1 + math.exp(-(life + field)))

        reward: float = score[Player.ME] - score[Player.OPPONENT]
        self._duel_cache = copy.deepcopy(self._duel_cache)
        return reward


    def _print_match_result(self, win_on_match: bool) -> None:
        result = ' win' if win_on_match else 'lose'
        win_rate: float = self._wins/(((self._match_count-1)%100)+1)
        print(f'Match {self._match_count:4d}: {result}, {win_rate:%}')
        if self._match_count % 100 == 0:
            self._wins = 0

    
    def _dump_match_result(self) -> None:
        if len(self._match_result) == 0:
            return
        now = datetime.datetime.now().isoformat(timespec='seconds').replace(':', '-')
        file = Path.cwd() / 'Decks' / self._deck.name / (now + '.csv')
        with file.open(mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(('match', 'win'))
            writer.writerows(enumerate(self._match_result))
        self._match_result.clear()
  
    
    def _update_usedflag(self, card_id: int) -> None:
        self._usedflag.used(card_id)


    def select_tp(self) -> bool:
        return True
        

    def select_mainphase_action(self, main: MainPhase) -> int:
        choices: list[Choice] = []

        for index, card in enumerate(main.summonable):
            choices.append(Choice(Action.SUMMON, index, card.id))
        
        for index, card in enumerate(main.special_summonable):
            choices.append(Choice(Action.SP_SUMMON, index, card.id))

        for index, card in enumerate(main.repositionable):
            choices.append(Choice(Action.REPOSITION, index, card.id))

        for index, card in enumerate(main.moster_settable):
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

        selected: Choice = self._brain.select(choices, self._duel, self._usedflag)    
        if selected.action is Action.ACTIVATE:
            self._update_usedflag(selected.card_id)

        return (selected.index << 16) + Action_to_int(selected.action)


    def select_battle_action(self, battle: BattlePhase) -> int:
        choices: list[Choice] = []

        for index, card in enumerate(battle.attackable):
            choices.append(Choice(Action.ATTACK, index, card.id))

        for index, card in enumerate(battle.activatable):
            desc: int = battle.activation_descs[index]
            choices.append(Choice(Action.ACTIVATE_IN_BATTLE, index, card.id, option=desc))

        if battle.can_main2:
            choices.append(Choice(Action.MAIN2))

        selected: Choice = self._brain.select(choices, self._duel, self._usedflag)
        if selected.action == Action.ACTIVATE_IN_BATTLE:
            self._update_usedflag(selected.card_id)

        return (selected.index << 16) + Action_to_int(selected.action)


    def select_effect_yn(self, card: Card, desc: int) -> bool:
        return True


    def select_yn(self) -> bool:
        return True


    def select_battle_replay(self) -> bool:
        return True

    
    def select_option(self, options: list[int]) -> int:
        return random.choice(list(range(len(options))))


    def select_card(self, cards: list[Card], min_: int, max_: int, cancelable: bool, hint: int) -> list[int]:
        choices: list[Choice] = []
        for index, card in enumerate(cards):
            choices.append(Choice(Action.SELECT, index, card.id, option=hint))

        num_to_select: int = max_ # ToDo: more intelligent
        selecteds: list[Choice] = []
        for _ in range(max_):
            selected: Choice = self._brain.select(choices, self._duel, self._usedflag)
            selecteds.append(selected)
            choices.remove(selected)
        return [selected.index for selected in selecteds]


    def select_chain(self, cards: list[Card], descriptions: list[int], forced: bool) -> int:
        choices: list[Choice] = []

        for index, card in enumerate(cards):
            desc = descriptions[index]
            choices.append(Choice(Action.CHAIN, index, card.id, desc))

        if not forced:
            choices.append(Choice(Action.CHAIN, -1, card_id=0, option=0)) # -1 means no activation

        selected: Choice = self._brain.select(choices, self._duel, self._usedflag)
        if selected.index != -1:
            self._update_usedflag(selected.card_id)

        return selected.index


    def select_place(self, player: Player, location: Location, selectable: int, is_pzone: bool) -> int:
        zones: list[Zone] = self._duel.field[player].where(location)
        choices: list[int] = [i for i, zone in enumerate(zones) if bool(selectable & zone.id)]
        ans: int = random.choice(choices)
        
        if is_pzone:
            ans = 6 if ans == 0 else 7

        return ans 


    def select_position(self, card_id: int, choices: list[CardPosition]) -> int:
        return int(choices[0])


    def select_tribute(self, choices: list[Card], min_: int, max_: int, cancelable: bool, hint: int) -> list[int]:
        my_card: list[Card] = sorted([card for card in choices if card.controller == Player.ME], key=lambda x:x.attack)
        op_card: list[Card] = sorted([card for card in choices if card.controller == Player.OPPONENT], key=lambda x:-x.attack)
        choosed: list[Card] = (op_card + my_card)[0:max_]
        return [choices.index(card) for card in choosed]
    

    def select_sum(self, choices: list[tuple[Card, int, int]], sum_value: int, min_: int, max_: int, must_just: bool, select_hint: int) -> list[int]:
        raise Exception('not complete coding')


    def select_unselect(self, choices: list[Card], min_: int, max_: int, cancelable: bool, hint: int):
        return self.select_card(choices, min_, max_, cancelable, hint)


    def select_counter(self, counter_type: int, quantity: int, cards: list[Card], counters: list[int]) -> list[int]:
        raise Exception('not complete coding')


    def select_number(self, choices: list[int]) -> int:
        raise Exception('not complete coding')

    
    def sort_card(self, cards: list[Card]) -> list[int]:
        raise Exception('not complete coding')


    def announce_attr(self, choices: list[Attribute], count: int) -> list[int]:
        raise Exception('not complete coding')


    def announce_race(self, choices: list[Race], count: int) -> list[int]:
        raise Exception('not complete coding')


        

def Action_to_int(action: Action) -> int:
    convert = {
        Action.SUMMON:     0,
        Action.SP_SUMMON:  1,
        Action.REPOSITION: 2,
        Action.SET_MONSTER:3,
        Action.SET_SPELL:  4,
        Action.ACTIVATE:   5,
        Action.BATTLE:     6,
        Action.END:        7,

        Action.ACTIVATE_IN_BATTLE: 0,
        Action.ATTACK:             1,
        Action.MAIN2:              2,
        Action.END_IN_BATTLE:      3,

        Action.CHAIN:  20,
        Action.SELECT: 21
    }
    return convert[action]