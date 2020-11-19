from typing import TypeVar
import numpy as np

from pyYGO.duel import Duel
from pyYGO.field import HalfField
from pyYGO.enums import CardPosition, Player
from pyYGO.wrapper import Position
from pyYGOAgent.deck import Deck
from pyYGOAgent.flags import UsedFlag
from pyYGOAgent.networkbase import Network

ndarray = TypeVar('ndarray')


class Network(Network):
    def backpropagate(self, factor: ndarray) -> None:
        der: ndarray = self._output_layer.derivative_activation_func(self._output_layer.input_cache)
        self._output_layer.delta =  der * factor
        for i in range(len(self._layer_structure)-2, 0, -1):
            self._calculate_deltas_for_hidden_layer(self._layers[i], self._layers[i+1])



class DuelNetwork(Network):
    def __init__(self) -> None:
        super().__init__([13, 8, 4])


    def outputs(self, duel: Duel) -> ndarray:
        turn_player: ndarray = np.array([int(duel.turn_player)], dtype='float64')
        phase: ndarray = np.array([(duel.phase >> i) & 1 for i in range(10)], dtype='float64')
        life: ndarray = np.array([duel.life[Player.ME], duel.life[Player.OPPONENT]], dtype='float64') / 8000
        inputs: ndarray = np.concatenate((turn_player, phase, life), axis=0)
        return self._outputs(inputs)



class LocationNetwork(Network):
    LOCATION_BIT: int = 10
    in_deck: ndarray     = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype='float64')
    in_hand: ndarray     = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype='float64')
    on_field: ndarray    = np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0], dtype='float64')
    in_GY: ndarray       = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0], dtype='float64')
    in_banished: ndarray = np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype='float64')
    in_side: ndarray     = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0], dtype='float64')
    not_in_deck: ndarray = np.array([0, 1, 1, 1, 1, 1, 0, 0, 0, 0], dtype='float64')
    inputs: ndarray

    def __init__(self, deck: Deck) -> None:
        self.deck: Deck = deck
        self.deck_list: list[int] = self.deck.main + self.deck.extra # ToDo: include side deck
        self.deck_list.sort()

        inputs_size: int = len(self.deck_list) * self.LOCATION_BIT
        layer_structure = [inputs_size, 720, 130, 4]
        super().__init__(layer_structure)

    
    def outputs(self, my_field: HalfField) -> ndarray:
        # set all card in deck 
        self.inputs: ndarray = np.concatenate([self.in_deck for _ in range(len(self.deck_list))], axis=0)

        for card in my_field.hand:
            index: int = self.get_index_of_inputs(card.id)
            if index != -1:
                self.inputs[index:index+self.LOCATION_BIT] = self.in_hand

        for zone in my_field.monster_zones:
            if not zone.has_card:
                continue
            index: int = self.get_index_of_inputs(zone.card.id)
            if index != -1:
                self.inputs[index:index+self.LOCATION_BIT] = self.on_field
                self.inputs[index+6:index+self.LOCATION_BIT] = self.position_array(zone.card.position)
            
        for zone in my_field.spell_zones:
            if not zone.has_card:
                continue
            index: int = self.get_index_of_inputs(zone.card.id)
            if index != -1:
                self.inputs[index:index+self.LOCATION_BIT] = self.on_field
                self.inputs[index+6:index+self.LOCATION_BIT] = self.position_array(zone.card.position)

        for card in my_field.graveyard:
            index: int = self.get_index_of_inputs(card.id)
            if index != -1:
                self.inputs[index:index+self.LOCATION_BIT] = self.in_GY
                self.inputs[index+6:index+self.LOCATION_BIT] = self.position_array(card.position)

        for card in my_field.banished:
            index: int = self.get_index_of_inputs(card.id)
            if index != -1:
                self.inputs[index:index+self.LOCATION_BIT] = self.in_banished
                self.inputs[index+6:index+self.LOCATION_BIT] = self.position_array(card.position)

        for side in self.deck.side:
            pass

        result: ndarray = self._outputs(self.inputs)
        return result
    

    def get_index_of_inputs(self, card_id: int) -> int:
        """
        return index for inputs array.
        if not found, return -1.
        """
        try:
            index: int = self.deck_list.index(card_id) * self.LOCATION_BIT
        except ValueError:
            return -1

        # for the same name card
        while self.inputs[index:index+self.LOCATION_BIT] @ self.not_in_deck:
            index += self.LOCATION_BIT

        return index


    def position_array(self, pos: Position) -> ndarray:
        POSITION = [
            CardPosition.FASEUP_ATTACK,
            CardPosition.FASEDOWN_ATTACK, 
            CardPosition.FASEUP_DEFENCE, 
            CardPosition.FASEDOWN_DEFENCE
        ]
        array: ndarray = np.array([bool(pos & p) for p in POSITION], dtype='float64')
        return array



class FlagNetwork(Network):
    def __init__(self, flag: UsedFlag) -> None:
        layer_structure = [flag.count, 65, 24, 4]
        super().__init__(layer_structure)

    
    def outputs(self, flag: UsedFlag) -> ndarray:
        inputs: ndarray = np.array([float(v) for v in flag.values()], dtype='float64')
        result: ndarray = self._outputs(inputs)
        return result



class OpponentNetwork(Network):
    def __init__(self) -> None:
        self.inputs_size: int = 5 + 36 * 13
        structure: list[int] = [self.inputs_size, 500, 150, 4]    
        super().__init__(structure)

    
    def outputs(self, opp_field: HalfField) -> ndarray:
        inputs: ndarray = np.zeros((self.inputs_size,), dtype='float64')
        inputs[0] = len(opp_field.deck) 
        inputs[1] = len(opp_field.hand) 
        inputs[2] = len(opp_field.graveyard) 
        inputs[3] = len(opp_field.banished) 
        inputs[4] = len(opp_field.extradeck) 

        POSITION = [
            CardPosition.FASEUP_ATTACK,
            CardPosition.FASEDOWN_ATTACK, 
            CardPosition.FASEUP_DEFENCE, 
            CardPosition.FASEDOWN_DEFENCE
        ]

        for i, zone in enumerate(opp_field.monster_zones):
            if zone.has_card:
                id: list[int] = [(zone.card.id >> j) & 1 for j in range(32)] # card id is 32 bits 
                pos: list[bool] = [bool(zone.card.position & pos) for pos in POSITION]
                inputs[5+36*i:5+36*(i+1)] = np.array(id+pos, dtype='float64')
            
        for i, zone in enumerate(opp_field.spell_zones):
            if zone.has_card:
                id: list[int] = [(zone.card.id >> j) & 1 for j in range(32)] # card id is 32 bits 
                pos: list[bool] = [bool(zone.card.position & pos) for pos in POSITION]
                inputs[257+36*i:257+36*(i+1)] = np.array(id+pos, dtype='float64')

        result: ndarray = self._outputs(inputs)
        return result


