from .networkbase_cpp import cNetwork
import numpy as np




class Network(cNetwork):
    _ActivationFuncCode = {
        'tanh':    1,
        'sigmoid': 2,
        'linear':  3
    }
    def __init__(self, layer_structure: list[int], learning_rate: float, activation_funcs: list[str]=None) -> None:
        if activation_funcs is None:
            activation_funcs = ['tanh' for _ in layer_structure]
        activation_func_codes = self._create_activation_func_codes(activation_funcs)
        super().__init__(layer_structure, learning_rate, activation_func_codes)

    
    def outputs(self, input_: np.ndarray) -> np.ndarray:
        return super().outputs(input_)

    
    def train(self, inputs: list[np.ndarray], expecteds: list[np.ndarray], epoch: int=1) -> None:
        super().trainForEpoch(inputs, expecteds, epoch)


    def _create_activation_func_codes(self, activation_funcs: list[str]) -> list[int]:
        activation_func_codes = []
        for s in activation_funcs:
            if s is None:
                activation_func_codes.append(self._ActivationFuncCode['tanh'])
                continue
            if s in self._ActivationFuncCode:
                activation_func_codes.append(self._ActivationFuncCode[s])
            else:
                raise ValueError('invalid activation function {}'.format(s))
        return activation_func_codes
            
            
