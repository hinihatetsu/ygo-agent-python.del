import random

from pyYGO.duel import Duel
from pyYGO.card import Card
from pyYGO.zone import Zone
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import CardPosition, Player, CardLocation, Attribute, Race
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action, ChainAction, MainAction, BattleAction, SelectAction
from pyYGOAgent.brain import AgentBrain
from pyYGOAgent.recorder import DecisionRecorder
from pyYGOAgent.flags import UsedFlag


class DuelAgent:
    TRAINING_INTERVAL: int = 10
    def __init__(self, deck_name: str, duel: Duel) -> None:
        self.deck: Deck = Deck(deck_name)
        self.duel: Duel = duel
        self.usedflag: UsedFlag = UsedFlag(self.deck)
        self.recorder: DecisionRecorder = DecisionRecorder(self.deck, self.duel, self.usedflag)
        self.brain: AgentBrain = AgentBrain(self.deck)

    
    def on_start(self) -> None:
        self.brain.on_start(self.duel, self.usedflag)
        self.recorder.reset_cache()

    
    def on_new_turn(self) -> None:
        self.usedflag.reset()
        if self.duel.turn_player == Player.ME:
            self.recorder.evaluate()


    def on_win(self) -> None:
        self.recorder.evaluate()

    
    def update_usedflag(self, card_id: int) -> None:
        self.usedflag.used(card_id)
        

    def select_mainphase_action(self, main: MainPhase) -> int:
        value: float = 0
        evaluated: list[MainAction] = []

        for index, card in enumerate(main.summonable):
            value = self.brain.evaluate_summon(card.id)
            evaluated.append(MainAction(value, Action.SUMMON, index, card.id))
        
        for index, card in enumerate(main.special_summonable):
            value = self.brain.evaluate_special_summon(card.id)
            evaluated.append(MainAction(value, Action.SP_SUMMON, index, card.id))

        for index, card in enumerate(main.repositionable):
            value = -1
            if card.position & CardPosition.ATTACK:
                if card.attack * 2 < card.defence:
                    value = 1
            elif card.position & CardPosition.DEFENCE:
                if card.attack >= self.duel.life[Player.OPPONENT]:
                    value = 1
            evaluated.append(MainAction(value, Action.REPOSITION, index, card.id))

        for index, card in enumerate(main.moster_settable):
            value = self.brain.evaluate_set(card.id)
            evaluated.append(MainAction(value, Action.SET_MONSTER, index, card.id))

        for index, card in enumerate(main.spell_settable):
            value = self.brain.evaluate_set(card.id)
            evaluated.append(MainAction(value, Action.SET_SPELL, index, card.id))

        for index, card in enumerate(main.activatable):
            desc: int = main.activation_descs[index]
            value = self.brain.evaluate_activate(card.id, desc)
            evaluated.append(MainAction(value, Action.ACTIVATE, index, card.id, desc))

        if main.can_battle:
            value = self.brain.evaluate_phase()
            evaluated.append(MainAction(value, Action.BATTLE))

        if main.can_end:
            value = self.brain.evaluate_phase()
            evaluated.append(MainAction(value, Action.END))

        evaluated.sort(key=lambda x:x.value, reverse=True)
        selected: MainAction = evaluated[0]

        self.recorder.save_decision(selected.action, selected.card_id, selected.option)
        
        if selected.action == Action.ACTIVATE:
            self.update_usedflag(selected.card_id)

        return selected.to_int()


    def select_battle_action(self, battle: BattlePhase) -> int:
        value: float = 0
        evaluated: list[BattleAction] = []

        for index, card in enumerate(battle.attackable):
            value = self.brain.evaluate_attack(card.id)
            evaluated.append(BattleAction(value, Action.ATTACK, index, card.id))

        for index, card in enumerate(battle.activatable):
            desc: int = battle.activation_descs[index]
            value = self.brain.evaluate_activate(card.id, desc)
            evaluated.append(BattleAction(value, Action.ACTIVATE_IN_BATTLE, index, card.id, option=desc))

        if battle.can_main2:
            value = self.brain.evaluate_phase()
            evaluated.append(BattleAction(value, Action.MAIN2))

        evaluated.sort(key=lambda x:x.value, reverse=True)
        selected: BattleAction = evaluated[0]

        self.recorder.save_decision(selected.action, selected.card_id, selected.option)

        if selected.action == Action.ACTIVATE_IN_BATTLE:
            self.update_usedflag(selected.card_id)

        return selected.to_int()


    def select_effect_yn(self, card: Card, desc: int) -> bool:
        return True


    def select_yn(self) -> bool:
        return True


    def select_battle_replay(self) -> bool:
        return True

    
    def select_option(self, options: list[int]) -> int:
        return random.choice(list(range(len(options))))


    def select_card(self, choices: list[Card], min_: int, max_: int, cancelable: bool, hint: int) -> list[int]:
        value: float = 0
        evaluated: list[SelectAction] = []
        for index, card in enumerate(choices):
            value = self.brain.evaluate_selection(card.id, hint)
            evaluated.append(SelectAction(value, index, card.id, hint))

        evaluated.sort(key=lambda x:x.value, reverse=True)
        for selected in evaluated[:max_]:
            self.recorder.save_decision(selected.action, selected.card_id, selected.hint)

        return [selected.index for selected in evaluated][:max_]


    def select_chain(self, choices: list[Card], descriptions: list[int], forced: bool) -> int:
        value: float = 0
        evaluated: list[ChainAction] = []

        for index, card in enumerate(choices):
            desc: int = descriptions[index]
            value = self.brain.evaluate_chain(card.id, desc)
            evaluated.append(ChainAction(value, index, card.id, desc))

        if not forced:
            evaluated.append(ChainAction(-0.3, -1, card_id=0, desc=0)) # -1 means no activation

        evaluated.sort(key=lambda x:x.value, reverse=True)
        selected: ChainAction = evaluated[0]

        if selected.index != -1: # activate something
            self.recorder.save_decision(selected.action, selected.card_id, selected.desc)
            self.update_usedflag(selected.card_id)

        return selected.to_int()


    def select_place(self, player: Player, location: CardLocation, selectable: int, is_pzone: bool) -> int:
        zones: list[Zone] = self.duel.field[player].where(location)
        choices: list[int] = [i for i, zone in enumerate(zones) if bool(selectable & zone.id)]
        ans: int = random.choice(choices)
        
        if is_pzone:
            ans = 6 if ans == 0 else 7

        return ans 


    def select_position(self, card_id: int, choices: list[CardPosition]) -> int:
        return int(choices[0])


    def select_tribute(self, choices: list[Card], min_: int, max_: int, cancelable: bool, hint: int) -> int:
        my_card: list[Card] = sorted([card for card in choices if card.controller == Player.ME], key=lambda x:x.attack)
        op_card: list[Card] = sorted([card for card in choices if card.controller == Player.OPPONENT], key=lambda x:-x.attack)
        choosed: list[Card] = (op_card + my_card)[0:max_]
        return [choices.index(card) for card in choosed]
    

    def select_sum(self, choices: list[tuple[Card, tuple[int, int]]], sum_value: int, min_: int, max_: int, must_just: bool, hint: int) -> list[int]:
        raise Exception('not complete coding')


    def select_unselect(self, choices: list[Card], min_: int, max_: int, cancelable: bool, hint: int):
        return self.select_card(choices, min_, max_, cancelable, hint)


    def select_counter(self, counter_type: int, quantity: int, cards: list[int], counters: list[int]) -> list[int]:
        raise Exception('not complete coding')


    def select_number(self, choices: list[int]) -> int:
        raise Exception('not complete coding')

    
    def sort_card(self, cards: list[Card]) -> list[int]:
        raise Exception('not complete coding')


    def announce_attr(self, choices: list[Attribute], count: int) -> list[int]:
        raise Exception('not complete coding')


    def announce_race(self, choices: list[Race], count: int) -> list[int]:
        raise Exception('not complete coding')

    
    def train(self) -> None:
        self.brain.train()