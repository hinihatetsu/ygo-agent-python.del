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
        self._deck: Deck = deck
        self._brain_path: Path = Path.cwd() / 'Decks' / self._deck.name / (self._deck.name + '.brain')
        self._summon_network: SummonNetwork = None
        self._special_summon_network: SpecialSummonNetwork = None
        self._reposition_network: RepositionNetwork = None
        self._set_network: SetNetwork = None
        self._activate_network: ActivateNetwork = None
        self._chain_network: ChainNetwork = None
        self._select_network: SelectNetwork = None
        self._attack_network: AttackNetwork = None
        self._phase_network: PhaseNetwork = None
        self._load_networks()


    def _load_networks(self) -> None:
        if not self._brain_path.exists():
            self._create_networks()
            return

        with open(self._brain_path, mode='rb') as f:
            networks: list[ActionNetwork] = pickle.load(f)
        [
            self._summon_network,
            self._special_summon_network,
            self._reposition_network,
            self._set_network,
            self._activate_network,
            self._chain_network,
            self._select_network,
            self._attack_network,
            self._phase_network
        ] = networks


    def _save_networks(self) -> None:
        info: list = [
            self._summon_network,
            self._special_summon_network,
            self._reposition_network,
            self._set_network,
            self._activate_network,
            self._chain_network,
            self._select_network,
            self._attack_network,
            self._phase_network
        ]
        with open(self._brain_path, mode='wb') as f:
            pickle.dump(info, f)

    
    def _create_networks(self) -> None:
        self._summon_network = SummonNetwork(self._deck)
        self._special_summon_network = SpecialSummonNetwork(self._deck)
        self._reposition_network = RepositionNetwork(self._deck)
        self._set_network = SetNetwork(self._deck)
        self._activate_network = ActivateNetwork(self._deck)
        self._chain_network = ChainNetwork(self._deck)
        self._select_network = SelectNetwork(self._deck)
        self._attack_network = AttackNetwork(self._deck)
        self._phase_network = PhaseNetwork(self._deck)
        self._save_networks()


    def on_start(self, duel: Duel, usedflag: UsedFlag) -> None:
        self._duel = duel
        self._usedflag = usedflag


    def evaluate_summon(self, card_id: int) -> float:
        value: float = self._summon_network.outputs(card_id, self._duel, self._usedflag)
        return value


    def evaluate_special_summon(self, card_id: int) -> float:
        value: float = self._special_summon_network.outputs(card_id, self._duel, self._usedflag)
        return value

    
    def evaluate_reposition(self, card_id: int) -> float:
        value: float = self._reposition_network.outputs(card_id, self._duel, self._usedflag)
        return value

    
    def evaluate_set(self, card_id: int) -> float:
        value: float = self._set_network.outputs(card_id, self._duel, self._usedflag)
        return value


    def evaluate_activate(self, card_id: int, activation_desc: int) -> float:
        value: float = self._activate_network.outputs(card_id, activation_desc, self._duel, self._usedflag)
        return value
    

    def evaluate_phase(self) -> float:
        value: float = self._phase_network.outputs(self._duel, self._usedflag)
        return value


    def evaluate_attack(self, card_id: int) -> float:
        value: float = self._attack_network.outputs(card_id, self._duel, self._usedflag)
        return value
        

    def evaluate_chain(self, card_id: int, activation_desc: int) -> float:
        value: float = self._chain_network.outputs(card_id, activation_desc, self._duel, self._usedflag)
        return value


    def evaluate_selection(self, card_id: int, select_hint: int) -> float:
        value: float = self._select_network.outputs(card_id, select_hint, self._duel, self._usedflag)
        return value
    

    def train(self, decisions: list[Decision]) -> None:
        random.shuffle(decisions)
        expecteds: list[np.ndarray] = [np.array([dc.value], dtype='float64') for dc in decisions]
        for _ in range(self.EPOCH):    
            for dc, expected in zip(decisions, expecteds):  
                if dc.action == Action.SUMMON:
                    self._summon_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SP_SUMMON:
                    self._special_summon_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.REPOSITION:
                    self._reposition_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SET_MONSTER or dc.action == Action.SET_SPELL:
                    self._set_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.ACTIVATE or dc.action == Action.ACTIVATE_IN_BATTLE:
                    self._activate_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.CHAIN:
                    self._chain_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.SELECT:
                    self._select_network.train(dc.card_id, dc.option, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.ATTACK:
                    self._attack_network.train(dc.card_id, dc.duel, dc.usedflag, expected)

                elif dc.action == Action.BATTLE or dc.action == Action.END or dc.action == Action.MAIN2:
                    self._phase_network.train(dc.duel, dc.usedflag, expected)

                else:
                    assert True, 'elif　not coveraged'
    
        self._save_networks()


