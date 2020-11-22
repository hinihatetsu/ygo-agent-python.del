from abc import ABC, abstractclassmethod
import numpy as np

from pyYGO.duel import Duel
from pyYGO.field import HalfField
from pyYGO.enums import Player, CardPosition
from pyYGOAgent.deck import Deck
from pyYGOAgent.flags import UsedFlag
from pyYGOAgent.networkbase import Network


_LOCATION_BIT: int = 10
_IN_DECK: np.ndarray     = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype='float64')
_IN_HAND: np.ndarray     = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype='float64')
_ON_FIELD: np.ndarray    = np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0], dtype='float64')
_IN_GY: np.ndarray       = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0], dtype='float64')
_IN_BANISHED: np.ndarray = np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype='float64')
_IN_SIDE: np.ndarray     = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0], dtype='float64')
_NOT_IN_DECK: np.ndarray = np.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0], dtype='float64')



class ActionNetwork(ABC):
    def __init__(self, deck: Deck) -> None:
        self._deck: Deck = deck
        self._deck_list: list[int] = deck.main + deck.extra # ToDo: add side deck
        self._deck_list.sort()
        size: int = self._input_size
        self._network: Network = Network([size, size * 2 // 3, 1])

    @property
    @abstractclassmethod
    def _input_size(self) -> int:
        pass



class CardIDNetwork(ActionNetwork):
    def outputs(self, card_id: int, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: np.ndarray = self._create_inputs(card_id, duel, usedflag)
        value: float = self._network._outputs(inputs)[0]
        return value


    def train(self, card_id: int, duel: Duel, usedflag: UsedFlag, expected: np.ndarray) -> None:
        self.outputs(card_id, duel, usedflag)
        self._network._backpropagate(expected)
        self._network._update()

    @property
    def _input_size(self) -> int:
        return len(self._create_inputs(0, Duel(), UsedFlag(self._deck)))

    
    def _create_inputs(self, card_id: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id: np.ndarray = _create_card_id_array(card_id)
        inputs: np.ndarray = np.concatenate((id, _create_inputs_base(self, duel, usedflag)))
        return inputs



class SummonNetwork(CardIDNetwork):
    pass

    

class SpecialSummonNetwork(CardIDNetwork):
    pass



class RepositionNetwork(CardIDNetwork):
    pass



class SetNetwork(CardIDNetwork):
    pass



class ActivateNetwork(ActionNetwork):
    def outputs(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: np.ndarray = self._create_inputs(card_id, activation_desc, duel, usedflag)
        value: float = self._network._outputs(inputs)[0]
        return value


    def train(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag, expected: np.ndarray) -> None:
        self.outputs(card_id, activation_desc, duel, usedflag)
        self._network._backpropagate(expected)
        self._network._update()

    @property
    def _input_size(self) -> int:
        return len(self._create_inputs(0, 0, Duel(), UsedFlag(self._deck)))
    

    def _create_inputs(self, card_id: int,activation_desc: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id: np.ndarray = _create_card_id_array(card_id)
        desc: np.ndarray = np.array([(activation_desc >> i) & 1 for i in range(64)], dtype='float64')
        inputs: np.ndarray = np.concatenate((id, desc, _create_inputs_base(self, duel, usedflag)))
        return inputs
    
    

class AttackNetwork(CardIDNetwork):
    pass



class ChainNetwork(ActionNetwork):
    def outputs(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: np.ndarray = self._create_inputs(card_id, activation_desc, duel, usedflag)
        value: float = self._network._outputs(inputs)[0]
        return value

    
    def train(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag, expected: np.ndarray) -> None:
        self.outputs(card_id, activation_desc, duel, usedflag)
        self._network._backpropagate(expected)
        self._network._update()

    @property
    def _input_size(self) -> int:
        return len(self._create_inputs(0, 0, Duel(), UsedFlag(self._deck)))


    def _create_inputs(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id: np.ndarray = _create_card_id_array(card_id)
        desc: np.ndarray = np.array([(activation_desc >> i) & 1 for i in range(64)], dtype='float64')
        is_chain_target: np.ndarray = np.array([any([card.id == card_id for card in duel.chain_targets])], dtype='float64')
        chain_player: np.ndarray = np.array([int(duel.last_chain_player)], dtype='float64')
        chain: list[np.ndarray] = [np.zeros((32,)) for _ in range(2)]
        for i, card in enumerate(duel.current_chain):
            if i < 2: chain[i] = _create_card_id_array(card.id)
        inputs: np.ndarray = np.concatenate((id, desc, is_chain_target, chain_player, chain[0], chain[1], _create_inputs_base(self, duel, usedflag)))
        return inputs



class SelectNetwork(ActionNetwork):
    def outputs(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: np.ndarray = self._create_inputs(card_id, select_hint, duel, usedflag)
        value: float = self._network._outputs(inputs)[0]
        return value


    def train(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag, expected: np.ndarray) -> None:
        self.outputs(card_id, select_hint, duel, usedflag)
        self._network._backpropagate(expected)
        self._network._update()

    @property
    def _input_size(self) -> int:
        return len(self._create_inputs(0, 0, Duel(), UsedFlag(self._deck)))
    

    def _create_inputs(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id: np.ndarray = _create_card_id_array(card_id)
        hint: np.ndarray = np.array([(select_hint >> i) & 1 for i in range(10)], dtype='float64')
        inputs: np.ndarray = np.concatenate((id, hint, _create_inputs_base(self, duel, usedflag)))
        return inputs



class PhaseNetwork(ActionNetwork):
    def outputs(self, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: np.ndarray = self._create_inputs(duel, usedflag)
        value: float = self._network._outputs(inputs)[0]
        return value

    
    def train(self, duel: Duel, usedflag: UsedFlag, expected: np.ndarray) -> None:
        self.outputs(duel, usedflag)
        self._network._backpropagate(expected)
        self._network._update()

    @property
    def _input_size(self) -> int:
        return len(self._create_inputs(Duel(), UsedFlag(self._deck)))

    
    def _create_inputs(self, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        return _create_inputs_base(self, duel, usedflag)
        


def _create_inputs_base(network: ActionNetwork, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
    basic: np.ndarray = _create_basic(duel)
    loc: np.ndarray = _create_locations(network, duel.field.myside)
    flag: np.ndarray = _create_usedflag(usedflag)
    op: np.ndarray = _create_opfield(duel.field.opside)  
    inputs: np.ndarray = np.concatenate((basic, loc, flag, op))
    return inputs


def _create_basic(duel: Duel) -> np.ndarray:
    """create ndarray from basic duel state"""
    turn_player: list[float] = [float(duel.turn_player)]
    phase: list[float] = [(duel.phase >> i) & 1 for i in range(10)]
    life: list[float] = [duel.life[Player.ME] / 8000, duel.life[Player.OPPONENT] / 8000]
    return np.array(turn_player + phase + life, dtype='float64')


def _create_locations(network: ActionNetwork, my_field: HalfField) -> np.ndarray:
    """create ndarray from location and position of AI's cards"""
    # set all card as in deck 
    inputs: np.ndarray = np.concatenate([_IN_DECK for _ in range(len(network._deck_list))], axis=0)

    for card in my_field.hand:
        index: int = _get_index(network._deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_HAND

    for zone in my_field.monster_zones:
        if not zone.has_card:
            continue
        index: int = _get_index(network._deck_list, inputs, zone.card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _ON_FIELD
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(zone.card.position)
        
    for zone in my_field.spell_zones:
        if not zone.has_card:
            continue
        index: int = _get_index(network._deck_list, inputs, zone.card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _ON_FIELD
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(zone.card.position)

    for card in my_field.graveyard:
        index: int = _get_index(network._deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_GY
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(card.position)

    for card in my_field.banished:
        index: int = _get_index(network._deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_BANISHED
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(card.position)

    for side in network._deck.side:
        pass

    return inputs


def _get_index(deck_list: list[int], inputs: np.ndarray, card_id: int) -> int:
    """return index for inputs array. if not found, return -1."""
    try:
        index: int = deck_list.index(card_id) * _LOCATION_BIT
    except ValueError:
        return -1

    # for the same name card
    while inputs[index:index+_LOCATION_BIT] @ _NOT_IN_DECK:
        index += _LOCATION_BIT

    return index


def _create_position_array(pos: CardPosition) -> np.ndarray:
    """create 4 bits array of position"""
    return np.array([(pos >> i) & 1 for i in range(4)], dtype='float64')


def _create_usedflag(flag: UsedFlag) -> np.ndarray:
    """create ndarray from usedflag state"""
    return np.array([float(v) for v in flag.values()], dtype='float64')


def _create_opfield(op_field: HalfField) -> np.ndarray:
    """create ndarray from opponent field state"""
    num_cards: np.ndarray = np.zeros((5,), dtype='float64')
    num_cards[0] = len(op_field.deck)
    num_cards[1] = len(op_field.hand)
    num_cards[2] = len(op_field.graveyard)
    num_cards[3] = len(op_field.banished) 
    num_cards[4] = len(op_field.extradeck)

    zones: np.ndarray = np.zeros((36 * 13), dtype='float64')
    for i, zone in enumerate(op_field.monster_zones):
        if zone.has_card:
            zones[36*i:36*(i+1)-4] = _create_card_id_array(zone.card.id)
            zones[36*i+32:36*(i+1)] = _create_position_array(zone.card.position)
        
    for i, zone in enumerate(op_field.spell_zones):
        if zone.has_card:
            zones[36*(i+7):36*(i+8)-4] = _create_card_id_array(zone.card.id)
            zones[36*(i+7)+32:36*(i+8)] = _create_position_array(zone.card.position)

    return np.concatenate((num_cards, zones))


def _create_card_id_array(card_id: int) -> np.ndarray:
    return np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')


