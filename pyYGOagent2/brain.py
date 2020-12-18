import os
from pathlib import Path
import random
import pickle
import math
import enum
import concurrent.futures
from typing import NamedTuple
import numpy as np

from util import error
from pyYGO import Duel, Deck 
from .action import Action, Choice, EvaluatedChoice
from .flags import UsedFlag
from .ANN import (
    ActionNetwork, SummonNetwork, SpecialSummonNetwork, RepositionNetwork, SetNetwork,
    ActivateNetwork, AttackNetwork, ChainNetwork, SelectNetwork, PhaseNetwork
)
from .recorder import ActionRecorder, Memory
from debug_tools import measure_time


_VALID_NETWORK: set[type] = {
                    SummonNetwork,
                    SpecialSummonNetwork,
                    RepositionNetwork,
                    SetNetwork,
                    ActivateNetwork,
                    AttackNetwork,
                    ChainNetwork,
                    SelectNetwork,
                    PhaseNetwork
                }


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


class LearningData(NamedTuple):
    inputs: list[np.ndarray]
    expecteds: list[np.ndarray]


class AgentBrain:
    EPOCH: int = 20
    DISCOUNT_RATE = 0.95
    def __init__(self, deck: Deck) -> None:
        self._deck: Deck = deck
        self._brain_path: Path = Path.cwd() / 'Decks' / self._deck.name / (self._deck.name + '.brain')
        self._networks: dict[NetworkKey, ActionNetwork] = {} 
        self._target_networks: dict[NetworkKey, ActionNetwork] = {}
        self._recorder: ActionRecorder = ActionRecorder()
        self._load_networks()
        self._count_for_DDQN: int = 0


    def _load_networks(self) -> None:
        if not self._brain_path.exists():
            self._create_networks()
            self._copy_to_target_network()
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
        self._copy_to_target_network()
                
    
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

    
    def _copy_to_target_network(self) -> None:
        self._target_networks = self._networks.copy()


    def select(self, choices: list[Choice], duel: Duel, usedflag: UsedFlag) -> Choice:
        evaluated: list[EvaluatedChoice] = []
        for choice in choices:
            key: NetworkKey = _Action_to_NetworkKey(choice.action)
            network: ActionNetwork = self._networks[key]
            input_ = network.create_input(choice.card_id, choice.option, duel, usedflag)
            value = network.outputs(input_)
            evaluated.append(EvaluatedChoice(choice, value))

        best = max(evaluated, key=lambda x:x.value)
        selected = best.choice
        self._recorder.save(selected, choices, duel, usedflag)
        return selected

    
    def feedback(self, reward: float) -> None:
        self._recorder.reward(reward)


    def train(self) -> None:
        memories = self._recorder.sample()
        if len(memories) == 0:
            return
        if self._count_for_DDQN & 1:
            self._copy_to_target_network()
        NetworkKey_to_LearningData = self._parse_memories(memories)
        self._train_concurrently(NetworkKey_to_LearningData)
        self._count_for_DDQN += 1

    
    def clear_memory(self) -> None:
        self._recorder.clear()
        
            
    def _parse_memories(self, memories: list[Memory]) -> dict[NetworkKey, LearningData]:
        NetworkKey_to_LearningData: dict[NetworkKey, LearningData] = {key: LearningData([], []) for key in NetworkKey}
        for mem in memories:
            selected, _, state = mem.decision
            key = _Action_to_NetworkKey(selected.action)  
            NetworkKey_to_LearningData[key].inputs.append(self._networks[key].create_input(selected.card_id, selected.option, *state))
            NetworkKey_to_LearningData[key].expecteds.append(self._create_teacher(mem))
        
        return NetworkKey_to_LearningData
    

    def _create_teacher(self, memory: Memory) -> np.ndarray:
        selected, _, state = memory.decision
        key: NetworkKey = _Action_to_NetworkKey(selected.action)
        network: ActionNetwork = self._target_networks[key]
        value: float = network.outputs(network.create_input(selected.card_id, selected.option, *state))
        return np.array([memory.reward + self.DISCOUNT_RATE * value], dtype='float64')
        

    @measure_time
    def _train_concurrently(self, NetworkKey_to_LearningData: dict[NetworkKey, LearningData]) -> None:
        sorted_pair = sorted(NetworkKey_to_LearningData.items(), key=lambda x:len(x[1].inputs), reverse=True)
        with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()//2) as executor:
            future_to_NetworkKey = {executor.submit(_train, self._networks[key], data): key for key, data in sorted_pair}
            for future in concurrent.futures.as_completed(future_to_NetworkKey):
                key = future_to_NetworkKey[future]
                self._networks[key] = future.result()


def _train(network: ActionNetwork, data: LearningData) -> ActionNetwork:
        network.train(data.inputs, data.expecteds, AgentBrain.EPOCH)
        return network



def _Action_to_NetworkKey(action: Action) -> NetworkKey:
    if action == Action.SUMMON:
        key = NetworkKey.SUMMON

    elif action == Action.SP_SUMMON:
        key = NetworkKey.SPSUMMON

    elif action == Action.REPOSITION:
        key = NetworkKey.REPOSITION

    elif action == Action.SET_MONSTER or action == Action.SET_SPELL:
        key = NetworkKey.SET

    elif action == Action.ACTIVATE or action == Action.ACTIVATE_IN_BATTLE:
        key = NetworkKey.ACTIVATE

    elif action == Action.CHAIN:
        key = NetworkKey.CHAIN

    elif action == Action.SELECT:
        key = NetworkKey.SELECT

    elif action == Action.ATTACK:
        key = NetworkKey.ATTACK

    elif action == Action.BATTLE or action == Action.END or action == Action.MAIN2:
        key = NetworkKey.PHASE
        
    else:
        assert False, 'elif　not coveraged'
    
    return key
        




