from abc import ABC, abstractclassmethod
from typing import Any
import numpy as np

from pyYGO import Duel, Deck, HalfField
from pyYGO.enums import Player, CardPosition
from .flags import UsedFlag
from cnetworkbase import Network


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
        layer_structure = [size, size * 2 // 3, 200, 1]
        activation_funcs = [None, None, None, 'linear']
        self._network: Network = Network(layer_structure, learning_rate=0.01, activation_funcs=activation_funcs)

    @property
    def _input_size(self) -> int:
        return len(self.create_input(0, 0, Duel(), UsedFlag(self._deck)))


    @abstractclassmethod
    def create_input(self, card_id: int, option: Any, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        pass


    def outputs(self, input_: np.ndarray) -> float:
        return self._network.outputs(input_)[0]


    def train(self, inputs: list[np.ndarray], expecteds: list[np.ndarray], epoch: int) -> None:
        self._network.train(inputs, expecteds, epoch)
        





class CardIDNetwork(ActionNetwork):
    def create_input(self, card_id: int, not_used: Any, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id = _create_card_id_array(card_id)
        inputs = np.concatenate((id, _create_input_base(self, duel, usedflag)))
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
    def create_input(self, card_id: int,activation_desc: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id = _create_card_id_array(card_id)
        desc = np.unpackbits(np.array([activation_desc], dtype=np.uint64).view(np.uint8), bitorder='little')
        inputs = np.concatenate((id, desc, _create_input_base(self, duel, usedflag)))
        return inputs
    
    

class AttackNetwork(CardIDNetwork):
    pass



class ChainNetwork(ActionNetwork):
    def create_input(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id = _create_card_id_array(card_id)
        desc = np.unpackbits(np.array([activation_desc], dtype=np.uint64).view(np.uint8), bitorder='little')
        is_chain_target = np.array([any([card.id == card_id for card in duel.chain_targets])], dtype='float64')
        chain_player = np.array([float(duel.last_chain_player)])
        chain: list[np.ndarray] = [np.zeros((32,)) for _ in range(2)]
        for i, card in enumerate(duel.current_chain):
            if i < 2: chain[i] = _create_card_id_array(card.id)
        inputs: np.ndarray = np.concatenate((id, desc, is_chain_target, chain_player, chain[0], chain[1], _create_input_base(self, duel, usedflag)))
        return inputs



class SelectNetwork(ActionNetwork):
    def create_input(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id = _create_card_id_array(card_id)
        hint = np.unpackbits(np.array([select_hint], dtype=np.uint64).view(np.uint8), bitorder='little')
        inputs = np.concatenate((id, hint, _create_input_base(self, duel, usedflag)))
        return inputs



class PhaseNetwork(ActionNetwork):
    def create_input(self, not_used: int, not_used_2: Any, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        return _create_input_base(self, duel, usedflag)
        


def _create_input_base(network: ActionNetwork, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
    basic: np.ndarray = _create_basic(duel)
    loc: np.ndarray = _create_locations(network, duel.field.myside)
    flag: np.ndarray = _create_usedflag(usedflag)
    op: np.ndarray = _create_opfield(duel.field.opside)  
    inputs: np.ndarray = np.concatenate((basic, loc, flag, op))
    return inputs


def _create_basic(duel: Duel) -> np.ndarray:
    """create ndarray from basic duel state"""
    turn_player: np.ndarray = np.array([duel.turn_player])
    phase: np.ndarray = np.unpackbits(np.array([duel.phase], dtype=np.uint16).view(np.uint8), count=-6, bitorder='little')
    life: np.ndarray = np.array([duel.life[Player.ME] / 8000, duel.life[Player.OPPONENT] / 8000], dtype='float64')
    return np.concatenate((turn_player, phase, life))


def _create_locations(network: ActionNetwork, my_field: HalfField) -> np.ndarray:
    """create ndarray from location and position of AI's cards"""
    # set all card as in deck 
    inputs: np.ndarray = np.concatenate([_IN_DECK for _ in range(len(network._deck_list))], axis=0)

    for card in my_field.hand:
        index = _get_index(network._deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_HAND

    for mzone in my_field.monster_zones:
        if not mzone.has_card:
            continue
        index = _get_index(network._deck_list, inputs, mzone.card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _ON_FIELD
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(mzone.card.position)
        
    for szone in my_field.spell_zones:
        if not szone.has_card:
            continue
        index = _get_index(network._deck_list, inputs, szone.card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _ON_FIELD
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(szone.card.position)

    for card in my_field.graveyard:
        index = _get_index(network._deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_GY
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(card.position)

    for card in my_field.banished:
        index = _get_index(network._deck_list, inputs, card.id)
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
    return np.unpackbits(np.array([pos], dtype=np.uint8), count=-4, bitorder='little')


def _create_usedflag(flag: UsedFlag) -> np.ndarray:
    """create ndarray from usedflag state"""
    return np.array([float(v) for v in flag.values()], dtype='float64')


def _create_opfield(op_field: HalfField) -> np.ndarray:
    """create ndarray from opponent field state"""
    num_cards: np.ndarray = np.zeros((5,), dtype='float64')
    num_cards[0] = len(op_field.deck) / 40
    num_cards[1] = len(op_field.hand) / 5
    num_cards[2] = len(op_field.graveyard) / 10
    num_cards[3] = len(op_field.banished) / 10
    num_cards[4] = len(op_field.extradeck) / 15

    zones: np.ndarray = np.zeros((36 * 13), dtype='float64')
    for i, mzone in enumerate(op_field.monster_zones):
        if mzone.has_card:
            zones[36*i:36*(i+1)-4] = _create_card_id_array(mzone.card.id)
            zones[36*i+32:36*(i+1)] = _create_position_array(mzone.card.position)
        
    for i, szone in enumerate(op_field.spell_zones):
        if szone.has_card:
            zones[36*(i+7):36*(i+8)-4] = _create_card_id_array(szone.card.id)
            zones[36*(i+7)+32:36*(i+8)] = _create_position_array(szone.card.position)

    return np.concatenate((num_cards, zones))


def _create_card_id_array(card_id: int) -> np.ndarray:
    return np.unpackbits(np.array([card_id], dtype=np.uint32).view(np.uint8), bitorder='little')


