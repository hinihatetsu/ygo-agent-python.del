import random
import pickle
from pathlib import Path
import numpy as np

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
    def __init__(self, deck: Deck) -> None:
        self.deck: Deck = deck
        self.duel: Duel = None
        self.usedflag: UsedFlag = None

        self.summon_networks: dict[int, SummonNetwork] = None
        self.special_summon_networks: dict[int, SpecialSummonNetwork] = None
        self.reposition_networks: dict[int, RepositionNetwork] = None
        self.set_networks: dict[int, SetNetwork] = None
        self.activate_networks: dict[int, ActivateNetwork] = None
        self.chain_networks: dict[int, ChainNetwork] = None
        self.select_network: SelectNetwork = None
        self.attack_networks: dict[int, AttackNetwork] = None
        self.phase_network: ActionNetwork = None

        self.load_networks()
        

    @property
    def brain_path(self) -> Path:
        return Path.cwd() / 'Decks' / self.deck.name / (self.deck.name + '.brain')

    @property
    def record_dir(self) -> Path:
        return Path.cwd() / 'Decks' / self.deck.name / 'Records'


    def load_networks(self) -> None:
        if not self.brain_path.exists():
            self.create_networks()
            return

        with open(self.brain_path, mode='rb') as f:
            networks: list = pickle.load(f)

        self.summon_networks = networks[0]
        self.special_summon_networks = networks[1]
        self.reposition_networks = networks[2]
        self.set_networks = networks[3]
        self.activate_networks = networks[4]
        self.chain_networks = networks[5]
        self.select_network = networks[6]
        self.attack_networks = networks[7]
        self.phase_network = networks[8]


    def save_networks(self) -> None:
        info: list = [
            self.summon_networks,
            self.special_summon_networks,
            self.reposition_networks,
            self.set_networks,
            self.activate_networks,
            self.chain_networks,
            self.select_network,
            self.attack_networks,
            self.phase_network
        ]

        with open(self.brain_path, mode='wb') as f:
            pickle.dump(info, f)

    
    def create_networks(self) -> None:
        self.summon_networks: dict[int, SummonNetwork] = dict()
        self.special_summon_networks: dict[int, SpecialSummonNetwork] = dict()
        self.reposition_networks: dict[int, RepositionNetwork] = dict()
        self.set_networks: dict[int, SetNetwork] = dict()
        self.activate_networks: dict[int, ActivateNetwork] = dict()
        self.chain_networks: dict[int, ChainNetwork] = dict()
        self.select_network: SelectNetwork = SelectNetwork(self.deck)
        self.attack_networks: dict[int, AttackNetwork] = dict()
        self.phase_network: ActionNetwork = ActionNetwork(self.deck)
        self.save_networks()


    def on_start(self, duel: Duel, usedflag: UsedFlag) -> None:
        self.duel = duel
        self.usedflag = usedflag


    def evaluate_summon(self, card: Card) -> float:
        if card.id not in self.summon_networks:
            self.summon_networks[card.id] = SummonNetwork(self.deck)
        value: float = self.summon_networks[card.id].outputs(self.duel, self.usedflag)
        return value


    def evaluate_special_summon(self, card: Card) -> float:
        if card.id not in self.special_summon_networks:
            self.special_summon_networks[card.id] = SpecialSummonNetwork(self.deck)
        value: float = self.special_summon_networks[card.id].outputs(self.duel, self.usedflag)
        return value

    
    def evaluate_reposition(self, card: Card) -> float:
        if card.id not in self.reposition_networks:
            self.reposition_networks[card.id] = RepositionNetwork(self.deck)
        value: float = self.reposition_networks[card.id].outputs(self.duel, self.usedflag)
        return value

    
    def evaluate_set(self, card: Card) -> float:
        if card.id not in self.set_networks:
            self.set_networks[card.id] = SetNetwork(self.deck)
        value: float = self.set_networks[card.id].outputs(self.duel, self.usedflag)
        return value


    def evaluate_activate(self, card: Card, activation_desc: int) -> float:
        if card.id not in self.activate_networks:
            self.activate_networks[card.id] = ActivateNetwork(self.deck)
        value: float = self.activate_networks[card.id].outputs(activation_desc, self.duel, self.usedflag)
        return value
    

    def evaluate_phase(self) -> float:
        value: float = self.phase_network.outputs(self.duel, self.usedflag)
        return value


    def evaluate_attack(self, card: Card) -> float:
        if card.id not in self.attack_networks:
            self.attack_networks[card.id] = AttackNetwork(self.deck)
        value: float = self.attack_networks[card.id].outputs(self.duel, self.usedflag)
        return value
        

    def evaluate_chain(self, card: Card, activation_desc: int) -> float:
        if card.id not in self.chain_networks:
            self.chain_networks[card.id] = ChainNetwork(self.deck)
        value: float = self.chain_networks[card.id].outputs(card.id, activation_desc, self.duel, self.usedflag)
        return value


    def evaluate_selection(self, card: Card, select_hint: int) -> float:
        value: float = self.select_network.outputs(card.id, select_hint, self.duel, self.usedflag)
        return value
    

    def train(self) -> None:
        dicisions: list[Dicision] = []
        for path in self.record_dir.glob('*.dicision'):
            with open(path, mode='rb') as f:
                dicisions.append(pickle.load(f))

        for _ in range(self.EPOCH):
            random.shuffle(dicisions)
            for dc in dicisions:
                expected: np.ndarray = np.array([dc.value], dtype='float64')
                if dc.action == Action.SUMMON:
                    self.summon_networks[dc.card_id].train(dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SP_SUMMON:
                    self.special_summon_networks[dc.card_id].train(dc.duel, dc.usedflag, expected)

                elif dc.action == Action.REPOSITION:
                    self.reposition_networks[dc.card_id].train(dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SET_MONSTER or dc.action == Action.SET_SPELL:
                    self.set_networks[dc.card_id].train(dc.duel, dc.usedflag, expected)

                elif dc.action == Action.ACTIVATE or dc.action == Action.ACTIVATE_IN_BATTLE:
                    self.activate_networks[dc.card_id].train(dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.CHAIN:
                    self.chain_networks[dc.card_id].train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SELECT:
                    self.select_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.ATTACK:
                    self.attack_networks[dc.card_id].train(dc.duel, dc.usedflag, expected)

                elif dc.action == Action.BATTLE or dc.action == Action.END or dc.action == Action.MAIN2:
                    self.phase_network.train(dc.duel, dc.usedflag, expected)

        
        self.save_networks()

        for path in self.record_dir.glob('*.dicision'):
            path.unlink()




