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
_POSITION: list[CardPosition] = [CardPosition.FASEUP_ATTACK, CardPosition.FASEDOWN_ATTACK, CardPosition.FASEUP_DEFENCE, CardPosition.FASEDOWN_DEFENCE]

class ActionNetwork:
    def __init__(self, deck: Deck) -> None:
        self.deck: Deck = deck
        self._deck_list: list[int] = self.deck.main + self.deck.extra # ToDo: add side deck
        size: int = self._input_size
        self._network: Network = Network([size, size * 2 // 3, 1])

        
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
        return len(self._create_inputs(Duel(), UsedFlag(self.deck)))
    

    def _create_inputs(self, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        basic: np.ndarray = self._create_basic(duel)
        loc: np.ndarray = self._create_locations(duel.field.myside)
        flag: np.ndarray = self._create_usedflag(usedflag)
        op: np.ndarray = self._create_opfield(duel.field.opside)
        
        inputs: np.ndarray = np.concatenate((basic, loc, flag, op))
        return inputs


    def _create_basic(self, duel: Duel) -> np.ndarray:
        """create ndarray from basic duel information"""
        turn_player: list[float] = [float(duel.turn_player)]
        phase: list[float] = [(duel.phase >> i) & 1 for i in range(10)]
        life: list[float] = [duel.life[Player.ME] / 8000, duel.life[Player.OPPONENT] / 8000]
        return np.array(turn_player + phase + life, dtype='float64')


    def _create_locations(self, my_field: HalfField) -> np.ndarray:
        """create ndarray from location and position of AI's cards"""
        # set all card as in deck 
        inputs: np.ndarray = np.concatenate([_IN_DECK for _ in range(len(self._deck_list))], axis=0)

        for card in my_field.hand:
            index: int = self._get_index(inputs, card.id)
            if index != -1:
                inputs[index:index+_LOCATION_BIT] = _IN_HAND

        for zone in my_field.monster_zones:
            if not zone.has_card:
                continue
            index: int = self._get_index(inputs, zone.card.id)
            if index != -1:
                inputs[index:index+_LOCATION_BIT] = _ON_FIELD
                self._set_position(inputs, index, zone.card.position)
            
        for zone in my_field.spell_zones:
            if not zone.has_card:
                continue
            index: int = self._get_index(inputs, zone.card.id)
            if index != -1:
                inputs[index:index+_LOCATION_BIT] = _ON_FIELD
                self._set_position(inputs, index, zone.card.position)

        for card in my_field.graveyard:
            index: int = self._get_index(inputs, card.id)
            if index != -1:
                inputs[index:index+_LOCATION_BIT] = _IN_GY
                self._set_position(inputs, index, card.position)

        for card in my_field.banished:
            index: int = self._get_index(inputs, card.id)
            if index != -1:
                inputs[index:index+_LOCATION_BIT] = _IN_BANISHED
                self._set_position(inputs, index, card.position)

        for side in self.deck.side:
            pass

        return inputs


    def _get_index(self, inputs: np.ndarray, card_id: int) -> int:
        """return index for inputs array. if not found, return -1."""
        try:
            index: int = self._deck_list.index(card_id) * _LOCATION_BIT
        except ValueError:
            return -1

        # for the same name card
        while inputs[index:index+_LOCATION_BIT] @ _NOT_IN_DECK:
            index += _LOCATION_BIT

        return index


    def _set_position(self, inputs: np.ndarray, index: int, pos: CardPosition) -> np.ndarray:
        for i, p in enumerate(_POSITION):
            inputs[index+6+i] = float(pos & p)

    
    def _create_usedflag(self, flag: UsedFlag) -> np.ndarray:
        """create ndarray from usedflag"""
        return np.array([float(v) for v in flag.values()], dtype='float64')

    
    def _create_opfield(self, op_field: HalfField) -> np.ndarray:
        """create ndarray from opponent field"""
        return np.zeros((1,))
    


class SummonNetwork(ActionNetwork):
    pass

    

class SpecialSummonNetwork(ActionNetwork):
    pass



class RepositionNetwork(ActionNetwork):
    pass



class SetNetwork(ActionNetwork):
    pass



class ActivateNetwork(ActionNetwork):
    def outputs(self, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: np.ndarray = self._create_inputs(activation_desc, duel, usedflag)
        value: float = self._network._outputs(inputs)[0]
        return value


    def train(self, activation_desc: int, duel: Duel, usedflag: UsedFlag, expected: np.ndarray) -> None:
        self.outputs(activation_desc, duel, usedflag)
        self._network._backpropagate(expected)
        self._network._update()

    @property
    def _input_size(self) -> int:
        return len(self._create_inputs(0, Duel(), UsedFlag(self.deck)))
    

    def _create_inputs(self, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        desc: np.ndarray = np.array([(activation_desc >> i) & 1 for i in range(64)], dtype='float64')
        inputs: np.ndarray = np.concatenate((super()._create_inputs(duel, usedflag), desc))
        return inputs
    
    

class AttackNetwork(ActionNetwork):
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
        return len(self._create_inputs(0, 0, Duel(), UsedFlag(self.deck)))


    def _create_inputs(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        desc: np.ndarray = np.array([(activation_desc >> i) & 1 for i in range(64)], dtype='float64')
        is_chain_target: np.ndarray = np.array([any([card.id == card_id for card in duel.chain_targets])], dtype='float64')
        chain_player: np.ndarray = np.array([int(duel.last_chain_player)], dtype='float64')
        chain: list[np.ndarray] = [np.zeros((32,), dtype='float64') for _ in range(2)]
        for i, card in enumerate(reversed(duel.current_chain)):
            if i > 1:
                break
            chain[i] = np.array([(card.id >> j) & 1 for j in range(32)], dtype='float64')
        inputs: np.ndarray = np.concatenate((super()._create_inputs(duel, usedflag), desc, is_chain_target, chain_player, chain[0], chain[1]))
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
        return len(self._create_inputs(0, 0, Duel(), UsedFlag(self.deck)))
    

    def _create_inputs(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag) -> np.ndarray:
        id: np.ndarray = np.array([(card_id >> j) & 1 for j in range(32)])
        hint: np.ndarray = np.array([(select_hint >> i) & 1 for i in range(10)], dtype='float64')
        inputs: np.ndarray = np.concatenate((super()._create_inputs(duel, usedflag), id, hint))
        return inputs



        