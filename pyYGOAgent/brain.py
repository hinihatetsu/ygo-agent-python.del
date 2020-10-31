import random
import pickle
from pathlib import Path
from typing import List, TypeVar
import numpy as np
ndarray = TypeVar('ndarray')

from pyYGO.duel import Duel 
from pyYGO.card import Card
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action
from pyYGOAgent.flags import UsedFlag
from pyYGOAgent.CNN import ActionNetwork, SummonNetwork, SpecialSummonNetwork, RepositionNetwork, SetNetwork
from pyYGOAgent.CNN import ActivateNetwork, AttackNetwork, ChainNetwork, SelectNetwork
from pyYGOAgent.recorder import Dicision



class AgentBrain:
    TRAIN_TIMES: int = 10
    def __init__(self, deck: Deck, duel: Duel, usedflag: UsedFlag) -> None:
        self.deck: Deck = deck
        self.duel: Duel = duel
        self.usedflag: UsedFlag = usedflag

        self.brain_path: Path = Path.cwd() / 'Decks' / self.deck.name / (self.deck.name + '.brain')
        self.record_dir: Path = Path.cwd() / 'Decks' / self.deck.name / 'Records'

        self.summon_network: SummonNetwork = None
        self.special_summon_network: SpecialSummonNetwork = None
        self.reposition_network: RepositionNetwork = None
        self.set_network: SetNetwork = None
        self.activate_network: ActivateNetwork = None
        self.chain_network: ChainNetwork = None
        self.select_network: SelectNetwork = None
        self.attack_network: AttackNetwork = None
        self.phase_network: ActionNetwork = None

        self.load_networks()


    def load_networks(self) -> None:
        if not self.brain_path.exists():
            self.create_networks()
            return

        with open(self.brain_path, mode='rb') as f:
            networks: List[ActionNetwork] = pickle.load(f)

        self.summon_network = networks[0]
        self.special_summon_network = networks[1]
        self.reposition_network = networks[2]
        self.set_network = networks[3]
        self.activate_network = networks[4]
        self.chain_network = networks[5]
        self.select_network = networks[6]
        self.attack_network = networks[7]
        self.phase_network = networks[8]


    def save_networks(self) -> None:
        info: List[ActionNetwork] = [
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

    
    def create_networks(self) -> None:
        self.summon_network = SummonNetwork(self.deck, self.usedflag)
        self.special_summon_network = SpecialSummonNetwork(self.deck, self.usedflag)
        self.reposition_network = RepositionNetwork(self.deck, self.usedflag)
        self.set_network = SetNetwork(self.deck, self.usedflag)
        self.activate_network = ActivateNetwork(self.deck, self.usedflag)
        self.chain_network = ChainNetwork(self.deck, self.usedflag)
        self.select_network = SelectNetwork(self.deck, self.usedflag)
        self.attack_network = AttackNetwork(self.deck, self.usedflag)
        self.phase_network = ActionNetwork(self.deck, self.usedflag)
        self.save_networks()


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
    

    def train(self) -> None:
        dicisions: List[Dicision] = []
        for path in self.record_dir.glob('*.dicision'):
            with open(path, mode='rb') as f:
                dicisions.append(pickle.load(f))

        for _ in range(self.TRAIN_TIMES):
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




