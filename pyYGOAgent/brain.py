import random
import pickle
from pathlib import Path
import enum
import concurrent.futures
from typing import NamedTuple
import numpy as np

from util import error
from pyYGO import Duel, Deck 
from .action import Action
from .flags import UsedFlag
from .ANN import (
    ActionNetwork, SummonNetwork, SpecialSummonNetwork, RepositionNetwork, SetNetwork,
    ActivateNetwork, AttackNetwork, ChainNetwork, SelectNetwork, PhaseNetwork
)
from .recorder import Decision

import time

_VALID_NETWORK: list[type] = [
                    SummonNetwork,
                    SpecialSummonNetwork,
                    RepositionNetwork,
                    SetNetwork,
                    ActivateNetwork,
                    AttackNetwork,
                    ChainNetwork,
                    SelectNetwork,
                    PhaseNetwork
                ]


class NetworkKey(enum.Enum):
    SUMMON     = enum.auto()
    SPSUMMON   = enum.auto()
    REPOSITION = enum.auto()
    SET        = enum.auto()
    ACTIVATE   = enum.auto()
    CHAIN      = enum.auto()
    SELECT     = enum.auto()
    ATTACK     = enum.auto()
    PHASE      = enum.auto()


class AgentBrain:
    EPOCH: int = 20
    def __init__(self, deck: Deck) -> None:
        self._deck: Deck = deck
        self._brain_path: Path = Path.cwd() / 'Decks' / self._deck.name / (self._deck.name + '.brain')
        self._networks: dict[NetworkKey, ActionNetwork] = {} 
        self._load_networks()


    def _load_networks(self) -> None:
        if not self._brain_path.exists():
            self._create_networks()
            return

        with open(self._brain_path, mode='rb') as f:
            networks: dict[NetworkKey, ActionNetwork] = pickle.load(f)
        broken: bool = type(networks) != dict
        if not broken:
            for key, network in networks.items():
                broken = key not in NetworkKey
                broken = type(network) not in _VALID_NETWORK
        if broken:
            error(f'{self._brain_path} file is broken. Delete it')
        
        self._networks = networks
                
    
    def _create_networks(self) -> None:
        self._networks[NetworkKey.SUMMON]     = SummonNetwork(self._deck)
        self._networks[NetworkKey.SPSUMMON]   = SpecialSummonNetwork(self._deck)
        self._networks[NetworkKey.REPOSITION] = RepositionNetwork(self._deck)
        self._networks[NetworkKey.SET]        = SetNetwork(self._deck)
        self._networks[NetworkKey.ACTIVATE]   = ActivateNetwork(self._deck)
        self._networks[NetworkKey.CHAIN]      = ChainNetwork(self._deck)
        self._networks[NetworkKey.SELECT]     = SelectNetwork(self._deck)
        self._networks[NetworkKey.ATTACK]     = AttackNetwork(self._deck)
        self._networks[NetworkKey.PHASE]      = PhaseNetwork(self._deck)


    def save_networks(self) -> None:
        with open(self._brain_path, mode='wb') as f:
            pickle.dump(self._networks, f)
        

    def on_start(self, duel: Duel, usedflag: UsedFlag) -> None:
        self._duel = duel
        self._usedflag = usedflag


    def evaluate_summon(self, card_id: int) -> float:
        input_ = self._networks[NetworkKey.SUMMON].create_input(card_id, None, self._duel, self._usedflag)
        return self._networks[NetworkKey.SUMMON].outputs(input_)


    def evaluate_special_summon(self, card_id: int) -> float:
        input_ = self._networks[NetworkKey.SPSUMMON].create_input(card_id, None, self._duel, self._usedflag)
        return self._networks[NetworkKey.SPSUMMON].outputs(input_)

    
    def evaluate_reposition(self, card_id: int) -> float:
        input_ = self._networks[NetworkKey.REPOSITION].create_input(card_id, None, self._duel, self._usedflag)
        return self._networks[NetworkKey.REPOSITION].outputs(input_)
    

    def evaluate_set(self, card_id: int) -> float:
        input_ = self._networks[NetworkKey.SET].create_input(card_id, None, self._duel, self._usedflag)
        return self._networks[NetworkKey.SET].outputs(input_)


    def evaluate_activate(self, card_id: int, activation_desc: int) -> float:
        input_ = self._networks[NetworkKey.ACTIVATE].create_input(card_id, activation_desc, self._duel, self._usedflag)
        return self._networks[NetworkKey.ACTIVATE].outputs(input_)
    

    def evaluate_phase(self) -> float:
        input_ = self._networks[NetworkKey.PHASE].create_input(None, None, self._duel, self._usedflag)
        return  self._networks[NetworkKey.PHASE].outputs(input_)


    def evaluate_attack(self, card_id: int) -> float:
        input_ = self._networks[NetworkKey.ATTACK].create_input(card_id, None, self._duel, self._usedflag)
        return self._networks[NetworkKey.ATTACK].outputs(input_)
        

    def evaluate_chain(self, card_id: int, activation_desc: int) -> float:
        input_ = self._networks[NetworkKey.CHAIN].create_input(card_id, activation_desc, self._duel, self._usedflag)
        return self._networks[NetworkKey.CHAIN].outputs(input_)


    def evaluate_selection(self, card_id: int, select_hint: int) -> float:
        input_ = self._networks[NetworkKey.SELECT].create_input(card_id, select_hint, self._duel, self._usedflag)
        return self._networks[NetworkKey.SELECT].outputs(input_)
    

    def train(self, decisions: list[Decision]) -> None:
        random.shuffle(decisions)
        expecteds: list[np.ndarray] = [np.array([dc.value]) for dc in decisions]
        learning_data: dict[NetworkKey, LearningData] = {key: LearningData([], []) for key in NetworkKey}
        for dc, expected in zip(decisions, expecteds):  
            if dc.action == Action.SUMMON:
                key = NetworkKey.SUMMON

            elif dc.action == Action.SP_SUMMON:
                key = NetworkKey.SPSUMMON

            elif dc.action == Action.REPOSITION:
                key = NetworkKey.REPOSITION

            elif dc.action == Action.SET_MONSTER or dc.action == Action.SET_SPELL:
                key = NetworkKey.SET

            elif dc.action == Action.ACTIVATE or dc.action == Action.ACTIVATE_IN_BATTLE:
                key = NetworkKey.ACTIVATE

            elif dc.action == Action.CHAIN:
                key = NetworkKey.CHAIN

            elif dc.action == Action.SELECT:
                key = NetworkKey.SELECT

            elif dc.action == Action.ATTACK:
                key = NetworkKey.ATTACK

            elif dc.action == Action.BATTLE or dc.action == Action.END or dc.action == Action.MAIN2:
                key = NetworkKey.PHASE
                
            else:
                assert False, 'elif　not coveraged'
            
            learning_data[key].inputs.append(self._networks[key].create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
            learning_data[key].expecteds.append(expected)

        sorted_pair = sorted(learning_data.items(), key=lambda x:len(x[1].inputs), reverse=True)
        t0 = time.time()
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            future_to_NetworkKey = {executor.submit(_train, self._networks[key], data): key for key, data in sorted_pair}
            for future in concurrent.futures.as_completed(future_to_NetworkKey):
                key = future_to_NetworkKey[future]
                self._networks[key] = future.result()
        t = time.time() - t0
        print('\ntotal: {:.2f} [s], {:.3f} [s] per epoch\n'.format(t, t/self.EPOCH))


class LearningData(NamedTuple):
    inputs: list[np.ndarray]
    expecteds: list[np.ndarray]


def _train(network: ActionNetwork, data: LearningData) -> ActionNetwork:
    network.train(data.inputs, data.expecteds, AgentBrain.EPOCH)
    return network