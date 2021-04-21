from typing import List

import numpy as np

from .action import Action
from .flags import UsedFlag
from pyYGO import Duel
from pyYGO.field import HalfField
from pyYGO.cardstatus import Position
from pyYGO.enums import Player


def create_state(action: Action, card_id: int, option: int, duel: Duel, usedflag: UsedFlag, deck_list: List[int]) -> np.ndarray:
    action_arr = np.unpackbits(np.array([int(action)], dtype=np.uint16).view(np.uint8), count=-7, bitorder='little')
    card_id_arr = _create_card_id_array(card_id)
    option_arr = np.unpackbits(np.array([option], dtype=np.uint32).view(np.uint8), bitorder='little')
    basic_arr = _create_basic_array(duel)
    loc_arr = _create_loc_array(deck_list, duel.field.myside)
    flag_arr = _create_usedflag_array(usedflag)
    op_arr = _create_opfield_array(duel.field.opside)  
    state = np.concatenate((action_arr, card_id_arr, option_arr, basic_arr, loc_arr, flag_arr, op_arr))
    return state.astype(np.float32)



def _create_basic_array(duel: Duel) -> np.ndarray:
    """create ndarray from basic duel state"""
    turn_player: np.ndarray = np.array([duel.turn_player])
    phase: np.ndarray = np.unpackbits(np.array([duel.phase], dtype=np.uint16).view(np.uint8), count=-6, bitorder='little')
    life: np.ndarray = np.array([duel.life[Player.ME] / 8000, duel.life[Player.OPPONENT] / 8000], dtype=np.float32)
    return np.concatenate((turn_player, phase, life))


_LOCATION_BIT: int = 10
_IN_DECK: np.ndarray     = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
_IN_HAND: np.ndarray     = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
_ON_FIELD: np.ndarray    = np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
_IN_GY: np.ndarray       = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0], dtype=np.float32)
_IN_BANISHED: np.ndarray = np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype=np.float32)
_IN_SIDE: np.ndarray     = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0], dtype=np.float32)
_NOT_IN_DECK: np.ndarray = np.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0], dtype=np.float32)

def _create_loc_array(deck_list: List[int], my_field: HalfField) -> np.ndarray:
    """create ndarray from location and position of AI's cards"""
    # set all card as in deck 
    inputs: np.ndarray = np.concatenate([_IN_DECK for _ in range(len(deck_list))], axis=0)

    for card in my_field.hand:
        index = _get_index(deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_HAND

    for mzone in my_field.monster_zones:
        if not mzone.has_card:
            continue
        index = _get_index(deck_list, inputs, mzone.card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _ON_FIELD
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(mzone.card.position)
        
    for szone in my_field.spell_zones:
        if not szone.has_card:
            continue
        index = _get_index(deck_list, inputs, szone.card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _ON_FIELD
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(szone.card.position)

    for card in my_field.graveyard:
        index = _get_index(deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_GY
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(card.position)

    for card in my_field.banished:
        index = _get_index(deck_list, inputs, card.id)
        if index != -1:
            inputs[index:index+_LOCATION_BIT] = _IN_BANISHED
            inputs[index+6:index+_LOCATION_BIT] = _create_position_array(card.position)

    return inputs


def _get_index(deck_list: List[int], inputs: np.ndarray, card_id: int) -> int:
    """ Return index for inputs array. if not found, return -1."""
    try:
        index: int = deck_list.index(card_id) * _LOCATION_BIT
    except ValueError:
        return -1

    # for the same name card
    while inputs[index:index+_LOCATION_BIT] @ _NOT_IN_DECK:
        index += _LOCATION_BIT

    return index


def _create_position_array(pos: Position) -> np.ndarray:
    """create 4 bits array of position"""
    return np.unpackbits(np.array([pos.value], dtype=np.uint8), count=-4, bitorder='little')


def _create_usedflag_array(flag: UsedFlag) -> np.ndarray:
    """create ndarray from usedflag state"""
    return np.array([float(v) for v in flag.values()], dtype=np.float32)


def _create_opfield_array(op_field: HalfField) -> np.ndarray:
    """create ndarray from opponent field state"""
    num_cards: np.ndarray = np.zeros((5,), dtype=np.float32)
    num_cards[0] = len(op_field.deck) / 40
    num_cards[1] = len(op_field.hand) / 5
    num_cards[2] = len(op_field.graveyard) / 10
    num_cards[3] = len(op_field.banished) / 10
    num_cards[4] = len(op_field.extradeck) / 15

    zones: np.ndarray = np.zeros((36 * 13), dtype=np.float32)
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