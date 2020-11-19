import random
import pickle
from pathlib import Path
from typing import TypeVar, NoReturn
import numpy as np
ndarray = TypeVar('ndarray')

from pyYGO.duel import Duel 
from pyYGO.card import Card
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action
from pyYGOAgent.flags import UsedFlag
from pyYGOAgent.ANN import ActionNetwork, SummonNetwork, SpecialSummonNetwork, RepositionNetwork, SetNetwork
from pyYGOAgent.ANN import ActivateNetwork, AttackNetwork, ChainNetwork, SelectNetwork
from pyYGOAgent.recorder import Dicision



class AgentBrain:
    EPOCH: int = 30
    def __init__(self, deck: Deck) -> NoReturn:
        self.duel: Duel = None
        self.usedflag: UsedFlag = None

        self.summon_network: SummonNetwork = None
        self.special_summon_network: SpecialSummonNetwork = None
        self.reposition_network: RepositionNetwork = None
        self.set_network: SetNetwork = None
        self.activate_network: ActivateNetwork = None
        self.chain_network: ChainNetwork = None
        self.select_network: SelectNetwork = None
        self.attack_network: AttackNetwork = None
        self.phase_network: ActionNetwork = None

        self.deck: Deck = deck

        
    @property
    def deck(self) ->Deck:
        return self._deck

    @deck.setter
    def deck(self, deck: Deck) -> NoReturn:
        self._deck = deck
        self.load_networks()

    @property
    def brain_path(self) -> Path:
        return Path.cwd() / 'Decks' / self.deck.name / (self.deck.name + '.brain')

    @property
    def record_dir(self) -> Path:
        return Path.cwd() / 'Decks' / self.deck.name / 'Records'


    def load_networks(self) -> NoReturn:
        if not self.brain_path.exists():
            self.create_networks()
            return

        with open(self.brain_path, mode='rb') as f:
            networks: list[ActionNetwork] = pickle.load(f)

        self.summon_network = networks[0]
        self.special_summon_network = networks[1]
        self.reposition_network = networks[2]
        self.set_network = networks[3]
        self.activate_network = networks[4]
        self.chain_network = networks[5]
        self.select_network = networks[6]
        self.attack_network = networks[7]
        self.phase_network = networks[8]


    def save_networks(self) -> NoReturn:
        info: list[ActionNetwork] = [
            self.summon_network,
            self.special_summon_network,
            self.reposition_network,
            self.set_network,
            self.activate_network,
            self.chain_network,
            self.select_network,
            self.attack_network,
            self.phase_network
        ]

        with open(self.brain_path, mode='wb') as f:
            pickle.dump(info, f)

    
    def create_networks(self) -> NoReturn:
        usedflag: UsedFlag = UsedFlag(self.deck)
        self.summon_network = SummonNetwork(self.deck, usedflag)
        self.special_summon_network = SpecialSummonNetwork(self.deck, usedflag)
        self.reposition_network = RepositionNetwork(self.deck, usedflag)
        self.set_network = SetNetwork(self.deck, usedflag)
        self.activate_network = ActivateNetwork(self.deck, usedflag)
        self.chain_network = ChainNetwork(self.deck, usedflag)
        self.select_network = SelectNetwork(self.deck, usedflag)
        self.attack_network = AttackNetwork(self.deck, usedflag)
        self.phase_network = ActionNetwork(self.deck, usedflag)
        self.save_networks()


    def on_start(self, duel: Duel, usedflag: UsedFlag) -> NoReturn:
        self.duel = duel
        self.usedflag = usedflag


    def evaluate_summon(self, card: Card) -> float:
        value: float = self.summon_network.outputs(card.id, self.duel, self.usedflag)
        return value


    def evaluate_special_summon(self, card: Card) -> float:
        value: float = self.special_summon_network.outputs(card.id, self.duel, self.usedflag)
        return value

    
    def evaluate_reposition(self, card: Card) -> float:
        value: float = self.reposition_network.outputs(card.id, self.duel, self.usedflag)
        return value

    
    def evaluate_set(self, card: Card) -> float:
        value: float = self.set_network.outputs(card.id, self.duel, self.usedflag)
        return value


    def evaluate_activate(self, card: Card, activation_desc: int) -> float:
        value: float = self.activate_network.outputs(card.id, activation_desc, self.duel, self.usedflag)
        return value
    

    def evaluate_phase(self) -> float:
        value: float = self.phase_network.outputs(self.duel, self.usedflag)
        return value


    def evaluate_attack(self, card: Card) -> float:
        value: float = self.attack_network.outputs(card.id, self.duel, self.usedflag)
        return value
        

    def evaluate_chain(self, card: Card, activation_desc: int) -> float:
        value: float = self.chain_network.outputs(card.id, activation_desc, self.duel, self.usedflag)
        return value


    def evaluate_selection(self, card: Card, select_hint: int) -> float:
        value: float = self.select_network.outputs(card.id, select_hint, self.duel, self.usedflag)
        return value
    

    def train(self) -> NoReturn:
        dicisions: list[Dicision] = []
        for path in self.record_dir.glob('*.dicision'):
            with open(path, mode='rb') as f:
                dicisions.append(pickle.load(f))

        for _ in range(self.EPOCH):
            random.shuffle(dicisions)
            for dc in dicisions:
                expected: ndarray = np.array([dc.value], dtype='float64')
                if dc.action == Action.SUMMON:
                    self.summon_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SP_SUMMON:
                    self.special_summon_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.REPOSITION:
                    self.reposition_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SET_MONSTER or dc.action == Action.SET_SPELL:
                    self.set_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.ACTIVATE or dc.action == Action.ACTIVATE_IN_BATTLE:
                    self.activate_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.CHAIN:
                    self.chain_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SELECT:
                    self.select_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.ATTACK:
                    self.attack_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.BATTLE or dc.action == Action.END or dc.action == Action.MAIN2:
                    self.phase_network.train(dc.duel, dc.usedflag, expected)

        
        self.save_networks()

        for path in self.record_dir.glob('*.dicision'):
            path.unlink()




