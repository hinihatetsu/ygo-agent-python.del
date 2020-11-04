from typing import List, TypeVar
import numpy as np
ndarray = TypeVar('ndarray')

from pyYGO.duel import Duel
from pyYGO.enums import Player
from pyYGOAgent.deck import Deck
from pyYGOAgent.flags import UsedFlag
from pyYGOAgent.network import Network, DuelNetwork, LocationNetwork, FlagNetwork, OpponentNetwork


class ActionNetwork:
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        self.final_decision_network: Network = Network([16, 10, 1]) # network for final dicision
        # basic parts
        self.duel_network: DuelNetwork = DuelNetwork()
        self.location_network: LocationNetwork = LocationNetwork(deck) # decide by location and position
        self.usedflag_network: FlagNetwork = FlagNetwork(usedflag) # decide by Used flags
        self.opponent_network: OpponentNetwork = OpponentNetwork() # decide by opponent field

    
    def get_inputs(self, duel: Duel, usedflag: UsedFlag) -> ndarray:
        outputs_duel: ndarray = self.duel_network.outputs(duel)
        outputs_loc: ndarray = self.location_network.outputs(duel.field[Player.ME])
        outputs_flag: ndarray = self.usedflag_network.outputs(usedflag)
        outputs_opp: ndarray = self.opponent_network.outputs(duel.field[Player.OPPONENT])
        inputs: ndarray = np.concatenate((outputs_duel, outputs_loc, outputs_flag, outputs_opp), axis=0)
        return inputs


    def outputs(self, duel: Duel, usedflag: UsedFlag) -> float:
        inputs: ndarray = self.get_inputs(duel, usedflag)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value

    
    def train(self, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()


class SummonNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 32, 32, 1])

    
    def outputs(self, card_id: int,  duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), id), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value


    def train(self, card_id: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()

    

class SpecialSummonNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 32, 32, 1])

    
    def outputs(self, card_id: int,  duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), id), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value


    def train(self, card_id: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()



class RepositionNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 32, 32, 1])

    
    def outputs(self, card_id: int,  duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), id), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value

    
    def train(self, card_id: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()



class SetNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 32, 32, 1])

    
    def outputs(self, card_id: int,  duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), id), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value

    
    def train(self, card_id: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()



class ActivateNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 8, 16, 1])
        self.activate_network: Network = Network([32 + 64, 64, 8])

    
    def outputs(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        desc: ndarray = np.array([(activation_desc >> i) & 1 for i in range(64)], dtype='float64')
        outputs_activate: ndarray = self.activate_network._outputs(np.concatenate((id, desc), axis=0))
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), outputs_activate), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value

    
    def train(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, activation_desc, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])
        self.activate_network.backpropagate(delta_factor[16:24])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()
        self.activate_network._update()




class AttackNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 32, 32, 1])

    
    def outputs(self, card_id: int, duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), id), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value

    
    def train(self, card_id: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()



class ChainNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 8, 16, 1])
        self.chain_network: Network = Network([32 + 64 + 2 + 32*2, 124, 8])

    
    def outputs(self, card_id: int, activation_desc: int, duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        desc: ndarray = np.array([(activation_desc >> i) & 1 for i in range(64)], dtype='float64')
        is_chain_target: ndarray = np.array([any([card.id == card_id for card in duel.chain_targets])], dtype='float64')
        chain_player: ndarray = np.array([int(duel.last_chain_player)], dtype='float64')
        chain: List[ndarray] = [np.zeros((32,), dtype='float64') for _ in range(2)]
        for i, card in enumerate(reversed(duel.current_chain)):
            if i > 1:
                break
            chain[i] = np.array([(card.id >> j) & 1 for j in range(32)], dtype='float64')

        inputs_chain: ndarray = np.concatenate((id, desc, is_chain_target, chain_player, chain[0], chain[1]), axis=0)
        outputs_chain: ndarray = self.chain_network._outputs(inputs_chain)

        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), outputs_chain), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value


    def train(self, card_id: int,  activation_desc: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, activation_desc, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])
        self.chain_network.backpropagate(delta_factor[16:24])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()
        self.chain_network._update()



class SelectNetwork(ActionNetwork):
    def __init__(self, deck: Deck, usedflag: UsedFlag) -> None:
        super().__init__(deck, usedflag)
        self.final_decision_network = Network([16 + 8, 16, 1])
        self.select_network: Network = Network([32 + 10, 28, 8])


    def outputs(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag) -> float:
        id: ndarray = np.array([(card_id >> i) & 1 for i in range(32)], dtype='float64')
        hint: ndarray = np.array([(select_hint >> i) & 1 for i in range(10)], dtype='float64')
        inputs_select: ndarray = np.concatenate((id, hint), axis=0)
        outputs_select: ndarray = self.select_network._outputs(inputs_select)
        inputs: ndarray = np.concatenate((self.get_inputs(duel, usedflag), outputs_select), axis=0)
        value: float = self.final_decision_network._outputs(inputs)[0]
        return value


    def train(self, card_id: int, select_hint: int, duel: Duel, usedflag: UsedFlag, expected: ndarray) -> None:
        self.outputs(card_id, select_hint, duel, usedflag)
        # backpropagation
        self.final_decision_network._backpropagate(expected) # original backpropagation in networkbase.py
        layer = self.final_decision_network._layers[1] # the first hidden layer of final_dicision_net
        delta_factor: ndarray = layer.delta @ layer.weight

        # following parameters depend on the concatenation in self.outputs()
        self.duel_network.backpropagate(delta_factor[0:4])
        self.location_network.backpropagate(delta_factor[4:8])
        self.usedflag_network.backpropagate(delta_factor[8:12])
        self.opponent_network.backpropagate(delta_factor[12:16])
        self.select_network.backpropagate(delta_factor[16:24])

        self.final_decision_network._update()
        self.duel_network._update()
        self.location_network._update()
        self.usedflag_network._update()
        self.opponent_network._update()
        self.select_network._update()



        