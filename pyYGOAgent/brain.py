import random
import pickle
from pathlib import Path
import concurrent.futures as concurrent
from typing import NamedTuple
import numpy as np

from pyYGO.duel import Duel 
from .deck import Deck
from .action import Action
from .flags import UsedFlag
from .ANN import (
    ActionNetwork, SummonNetwork, SpecialSummonNetwork, RepositionNetwork, SetNetwork,
    ActivateNetwork, AttackNetwork, ChainNetwork, SelectNetwork, PhaseNetwork
)
from .recorder import Decision

import time



class AgentBrain:
    EPOCH: int = 20
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
        #self._save_networks()


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


    def on_start(self, duel: Duel, usedflag: UsedFlag) -> None:
        self._duel = duel
        self._usedflag = usedflag


    def evaluate_summon(self, card_id: int) -> float:
        input_: np.ndarray = self._summon_network.create_input(card_id, None, self._duel, self._usedflag)
        return self._summon_network.outputs(input_)


    def evaluate_special_summon(self, card_id: int) -> float:
        input_: np.ndarray = self._special_summon_network.create_input(card_id, None, self._duel, self._usedflag)
        return self._special_summon_network.outputs(input_)

    
    def evaluate_reposition(self, card_id: int) -> float:
        input_: np.ndarray = self._reposition_network.create_input(card_id, None, self._duel, self._usedflag)
        return self._reposition_network.outputs(input_)
    

    def evaluate_set(self, card_id: int) -> float:
        input_: np.ndarray = self._set_network.create_input(card_id, None, self._duel, self._usedflag)
        return self._set_network.outputs(input_)


    def evaluate_activate(self, card_id: int, activation_desc: int) -> float:
        input_: np.ndarray = self._activate_network.create_input(card_id, activation_desc, self._duel, self._usedflag)
        return self._activate_network.outputs(input_)
    

    def evaluate_phase(self) -> float:
        input_: np.ndarray = self._phase_network.create_input(None, None, self._duel, self._usedflag)
        return  self._phase_network.outputs(input_)


    def evaluate_attack(self, card_id: int) -> float:
        input_: np.ndarray = self._attack_network.create_input(card_id, None, self._duel, self._usedflag)
        return self._attack_network.outputs(input_)
        

    def evaluate_chain(self, card_id: int, activation_desc: int) -> float:
        input_: np.ndarray = self._chain_network.create_input(card_id, activation_desc, self._duel, self._usedflag)
        return self._chain_network.outputs(input_)


    def evaluate_selection(self, card_id: int, select_hint: int) -> float:
        input_: np.ndarray = self._select_network.create_input(card_id, select_hint, self._duel, self._usedflag)
        return self._select_network.outputs(input_)
    

    def train(self, decisions: list[Decision]) -> None:
        random.shuffle(decisions)
        expecteds: list[np.ndarray] = [np.array([dc.value]) for dc in decisions]
        learning_info: dict[Action, LearningInfo] = {
            Action.SUMMON: LearningInfo(self._summon_network, [], []),
            Action.SP_SUMMON: LearningInfo(self._special_summon_network, [], []),
            Action.REPOSITION: LearningInfo(self._reposition_network, [], []),
            Action.SET_MONSTER: LearningInfo(self._set_network, [], []),
            Action.ACTIVATE: LearningInfo(self._activate_network, [], []),
            Action.CHAIN: LearningInfo(self._chain_network, [], []),
            Action.SELECT: LearningInfo(self._select_network, [], []),
            Action.ATTACK: LearningInfo(self._attack_network, [], []),
            Action.BATTLE: LearningInfo(self._phase_network, [], []),
        }
        for dc, expected in zip(decisions, expecteds):  
            if dc.action == Action.SUMMON:
                action = Action.SUMMON
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.SP_SUMMON:
                action = Action.SP_SUMMON
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.REPOSITION:
                action = Action.REPOSITION
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.SET_MONSTER or dc.action == Action.SET_SPELL:
                action = Action.SET_MONSTER
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.ACTIVATE or dc.action == Action.ACTIVATE_IN_BATTLE:
                action = Action.ACTIVATE
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.CHAIN:
                action = Action.CHAIN
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.SELECT:
                action = Action.SELECT
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.ATTACK:
                action = Action.ATTACK
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            elif dc.action == Action.BATTLE or dc.action == Action.END or dc.action == Action.MAIN2:
                action = Action.BATTLE
                network = learning_info[action].network
                learning_info[action].inputs.append(network.create_input(dc.card_id, dc.option, dc.duel, dc.usedflag))
                learning_info[action].expecteds.append(expected)

            else:
                assert True, 'elif　not coveraged'

        t0 = time.time()
        for info in learning_info.values():
            _train(info)
        t = time.time() - t0
        print('\ntotal: {:.2f} [s], {:.3f} per epoch\n'.format(t, t/self.EPOCH))
        #self._save_networks()


class LearningInfo(NamedTuple):
    network: ActionNetwork
    inputs: list[np.ndarray]
    expecteds: list[np.ndarray]


def _train(info: LearningInfo) -> None:
    print(f"\n{type(info.network)}")
    t0 = time.time()
    info.network.train(info.inputs, info.expecteds, AgentBrain.EPOCH)
    t1 = time.time()
    print("time: {:.2f} [s]".format(t1-t0))