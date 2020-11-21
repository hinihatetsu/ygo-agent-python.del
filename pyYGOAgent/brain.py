import random
import pickle
from pathlib import Path
import numpy as np

from pyYGO.duel import Duel 
from pyYGOAgent.deck import Deck
from pyYGOAgent.action import Action
from pyYGOAgent.flags import UsedFlag
from pyYGOAgent.ANN import ActionNetwork, SummonNetwork, SpecialSummonNetwork, RepositionNetwork, SetNetwork
from pyYGOAgent.ANN import ActivateNetwork, AttackNetwork, ChainNetwork, SelectNetwork, PhaseNetwork
from pyYGOAgent.recorder import Decision



class AgentBrain:
    EPOCH: int = 30
    def __init__(self, deck: Deck) -> None:
        self.deck: Deck = deck
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
        self.phase_network: PhaseNetwork = None

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


    def save_networks(self) -> None:
        info: list = [
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
        self.summon_network = SummonNetwork(self.deck)
        self.special_summon_network = SpecialSummonNetwork(self.deck)
        self.reposition_network = RepositionNetwork(self.deck)
        self.set_network = SetNetwork(self.deck)
        self.activate_network = ActivateNetwork(self.deck)
        self.chain_network = ChainNetwork(self.deck)
        self.select_network = SelectNetwork(self.deck)
        self.attack_network = AttackNetwork(self.deck)
        self.phase_network = PhaseNetwork(self.deck)
        self.save_networks()


    def on_start(self, duel: Duel, usedflag: UsedFlag) -> None:
        self.duel = duel
        self.usedflag = usedflag


    def evaluate_summon(self, card_id: int) -> float:
        value: float = self.summon_network.outputs(card_id, self.duel, self.usedflag)
        return value


    def evaluate_special_summon(self, card_id: int) -> float:
        value: float = self.special_summon_network.outputs(card_id, self.duel, self.usedflag)
        return value

    
    def evaluate_reposition(self, card_id: int) -> float:
        value: float = self.reposition_network.outputs(card_id, self.duel, self.usedflag)
        return value

    
    def evaluate_set(self, card_id: int) -> float:
        value: float = self.set_network.outputs(card_id, self.duel, self.usedflag)
        return value


    def evaluate_activate(self, card_id: int, activation_desc: int) -> float:
        value: float = self.activate_network.outputs(card_id, activation_desc, self.duel, self.usedflag)
        return value
    

    def evaluate_phase(self) -> float:
        value: float = self.phase_network.outputs(self.duel, self.usedflag)
        return value


    def evaluate_attack(self, card_id: int) -> float:
        value: float = self.attack_network.outputs(card_id, self.duel, self.usedflag)
        return value
        

    def evaluate_chain(self, card_id: int, activation_desc: int) -> float:
        value: float = self.chain_network.outputs(card_id, activation_desc, self.duel, self.usedflag)
        return value


    def evaluate_selection(self, card_id: int, select_hint: int) -> float:
        value: float = self.select_network.outputs(card_id, select_hint, self.duel, self.usedflag)
        return value
    

    def train(self) -> None:
        decisions: list[Decision] = []
        for path in self.record_dir.glob('*.decision'):
            with open(path, mode='rb') as f:
                decisions.append(pickle.load(f))

        for _ in range(self.EPOCH):
            random.shuffle(decisions)
            for dc in decisions:
                expected: np.ndarray = np.array([dc.value], dtype='float64')
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

        for path in self.record_dir.glob('*.decision'):
            path.unlink()




