import random
from typing import List

from pyYGO.duel import Duel
from pyYGO.card import Card
from pyYGO.zone import Zone
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import CardPosition, Player, CardLocation
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action, ChainAction, MainAction, BattleAction, SelectAction
from pyYGOAgent.brain import AgentBrain
from pyYGOAgent.recoder import DicisionRecorder
from pyYGOAgent.flags import UsedFlag


class DuelAgent:
    TRAINING_INTERVAL: int = 3
    def __init__(self, deck_name: str, duel: Duel) -> None:
        self.deck: Deck = Deck(deck_name)
        self.duel: Duel = duel
        self.usedflag: UsedFlag = UsedFlag(self.deck)
        self.recorder: DicisionRecorder = DicisionRecorder(self.deck, self.duel, self.usedflag)
        self.brain: AgentBrain = AgentBrain(self.deck, self.duel, self.usedflag)

    
    def start_new_game(self) -> None:
        self.brain.duel = self.duel
        self.brain.usedflag = self.usedflag
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
        evaluated: List[MainAction] = []

        for index, card in enumerate(main.summonable):
            value: float = self.brain.evaluate_summon(card)
            evaluated.append(MainAction(value, Action.SUMMON, index, card.id))
        
        for index, card in enumerate(main.special_summonable):
            value: float = self.brain.evaluate_special_summon(card)
            evaluated.append(MainAction(value, Action.SP_SUMMON, index, card.id))

        for index, card in enumerate(main.repositionable):
            value: float = self.brain.evaluate_reposition(card)
            evaluated.append(MainAction(value, Action.REPOSITION, index, card.id))

        for index, card in enumerate(main.moster_settable):
            value: float = self.brain.evaluate_set(card)
            evaluated.append(MainAction(value, Action.SET_MONSTER, index, card.id))

        for index, card in enumerate(main.spell_settable):
            value: float = self.brain.evaluate_set(card)
            evaluated.append(MainAction(value, Action.SET_SPELL, index, card.id))

        for index, card in enumerate(main.activatable):
            desc: int = main.activation_descs[index]
            value: float = self.brain.evaluate_activate(card, desc)
            evaluated.append(MainAction(value, Action.ACTIVATE, index, card.id, desc))

        if main.can_battle:
            value: float = self.brain.evaluate_phase()
            evaluated.append(MainAction(value, Action.BATTLE))

        if main.can_end:
            value: float = self.brain.evaluate_phase()
            evaluated.append(MainAction(value, Action.END))

        evaluated.sort(key=lambda x:x.value, reverse=True)
        selected: MainAction = evaluated[0]

        self.recorder.save_dicision(selected.action, selected.card_id, selected.option)
        
        if selected.action == Action.ACTIVATE:
            self.update_usedflag(selected.card_id)

        return selected.to_int()


    def select_battle_action(self, battle: BattlePhase) -> int:
        evaluated: List[BattleAction] = []

        for index, card in enumerate(battle.attackable):
            value: float = self.brain.evaluate_attack(card)
            evaluated.append(BattleAction(value, Action.ATTACK, index, card.id))

        for index, card in enumerate(battle.activatable):
            desc: int = battle.activation_descs[index]
            value: float = self.brain.evaluate_activate(card, desc)
            evaluated.append(BattleAction(value, Action.ACTIVATE_IN_BATTLE, index, card.id, option=desc))

        if battle.can_main2:
            value: float = self.brain.evaluate_phase()
            evaluated.append(BattleAction(value, Action.MAIN2))

        evaluated.sort(key=lambda x:x.value, reverse=True)
        selected: BattleAction = evaluated[0]

        self.recorder.save_dicision(selected.action, selected.card_id, selected.option)

        if selected.action == Action.ACTIVATE_IN_BATTLE:
            self.update_usedflag(selected.card_id)

        return selected.to_int()


    def select_effect_yn(self, card: Card, desc: int) -> bool:
        return True


    def select_yn(self) -> bool:
        return True


    def select_battle_replay(self) -> bool:
        return True

    
    def select_option(self, options: List[int]) -> int:
        return random.choice(list(range(len(options))))


    def select_card(self, choices: List[Card], min: int, max: int, cancelable: bool, hint: int) -> List[int]:
        evaluated: List[SelectAction] = []
        for index, card in enumerate(choices):
            value: float = self.brain.evaluate_selection(card, hint)
            evaluated.append(SelectAction(value, index, card.id, hint))

        evaluated.sort(key=lambda x:x.value, reverse=True)
        for selected in evaluated[:max]:
            self.recorder.save_dicision(selected.action, selected.card_id, selected.hint)

        return [selected.index for selected in evaluated][:max]


    def select_chain(self, choices: List[Card], descriptions: List[int], forced: bool) -> int:
        evaluated: List[ChainAction] = []

        for index, card in enumerate(choices):
            desc: int = descriptions[index]
            value: float = self.brain.evaluate_chain(card, desc)
            evaluated.append(ChainAction(value, index, card.id, desc))

        if not forced:
            evaluated.append(ChainAction(-0.3, -1, card_id=0, desc=0)) # -1 means no activation

        evaluated.sort(key=lambda x:x.value, reverse=True)
        selected: ChainAction = evaluated[0]

        if selected.index != -1: # activate something
            self.recorder.save_dicision(selected.action, selected.card_id, selected.desc)
            self.update_usedflag(selected.card_id)

        return selected.to_int()


    def select_place(self, player: Player, location: CardLocation, selectable: int, is_pzone: bool) -> int:
        zones: List[Zone] = self.duel.field[player][location]
        choices: List[int] = [i for i, zone in enumerate(zones) if bool(selectable & zone.id)]
        ans: int = random.choice(choices)
        
        if is_pzone:
            ans = 6 if ans == 0 else 7

        return ans 


    def select_position(self, card_id: int, choices: List[CardPosition]) -> int:
        return int(choices[0])


    def select_tribute(self, choices: List[Card], min: int, max: int, cancelable: bool, hint: int) -> int:
        my_card: List[Card] = sorted([card for card in choices if card.controller == Player.ME], key=lambda x:x.attack)
        op_card: List[Card] = sorted([card for card in choices if card.controller == Player.OPPONENT], key=lambda x:-x.attack)
        choosed: List[Card] = (op_card + my_card)[0:max]
        return [choices.index(card) for card in choosed]


    def select_unselect(self, choices: List[Card], min: int, max: int, cancelable: bool, hint: int):
        return self.select_card(choices, min, max, cancelable, hint)


    