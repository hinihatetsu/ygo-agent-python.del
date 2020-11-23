from functools import reduce
from typing import Callable
from pyYGOAgent.util import linear, derivative_linear, sigmoid, derivative_sigmoid, ReLU, derivative_ReLU, softmax, derivative_softmax, tanh, derivative_tanh
import numpy as np

der_act_funcs = {sigmoid: derivative_sigmoid,
                 linear: derivative_linear,
                 ReLU: derivative_ReLU,
                 softmax: derivative_softmax,
                 tanh: derivative_tanh}

class Layer:
    def __init__(self, num_inputs: int, num_neurons: int, learning_rate: float, act_func: Callable[[np.ndarray], np.ndarray], is_input_layer: bool=False) -> None:
        self.learning_rate: float = learning_rate
        self.weight: np.ndarray = np.random.randn(num_neurons, num_inputs) / np.sqrt(num_inputs)
        self.bias: np.ndarray = np.random.randn(num_neurons) / np.sqrt(num_neurons)
        self.delta: np.ndarray = np.zeros(num_neurons, dtype='float64')
        self.input_cache: np.ndarray = np.zeros(num_neurons)
        self.output_cache: np.ndarray = np.zeros(num_neurons)
        self.activation_func = act_func
        self.is_input_layer: bool = is_input_layer


    @property
    def activation_func(self) -> Callable[[np.ndarray], np.ndarray]:
        return self._activation_func
    
    @activation_func.setter
    def activation_func(self, func: Callable[[np.ndarray], np.ndarray]) -> None:
        self._activation_func = func
        self._derivative_activation_func = der_act_funcs[func]

    @property
    def derivative_activation_func(self) -> Callable[[np.ndarray], np.ndarray]:
        return self._derivative_activation_func 


    def outputs(self, inputs: np.ndarray) -> np.ndarray:    
        if self.is_input_layer:
            self.output_cache = inputs
        else:
            self.input_cache = self.weight @ inputs + self.bias
            self.output_cache = self.activation_func(self.input_cache)
        return self.output_cache


    def _calculate_deltas_for_output_layer(self, expected: np.ndarray) -> None:
        self.delta = self.derivative_activation_func(self.input_cache) * (self.output_cache - expected)

    
    def _calculate_deltas_for_hidden_layer(self, delta: np.ndarray) -> None:
        self.delta = self.derivative_activation_func(self.input_cache) * delta


class Network:
    def __init__(self, layer_structure: list[int], learning_rate: float=0.01, act_func: Callable[[np.ndarray], np.ndarray]=tanh) -> None:      
        self._layer_structure: list[int] = layer_structure
        self._size: int = len(self._layer_structure)
        self._layers: list[Layer] = [Layer(0, layer_structure[0], learning_rate, act_func, is_input_layer=True)]
        for n, m in zip(layer_structure, layer_structure[1:]):
            self._layers.append(Layer(n, m, learning_rate, act_func))
        
    @property
    def _layers_weights(self) -> list[np.ndarray]:
        return [layer.weight for layer in self._layers]

    @property
    def _output_layer(self) -> Layer:
        return self._layers[self._size-1]


    def _activate(self, inputs: np.ndarray, layer: Layer) -> np.ndarray:
        return layer.outputs(inputs)


    def _outputs(self, inputs: np.ndarray) -> np.ndarray:
        return reduce(self._activate, self._layers, inputs)


    def _backpropagate(self, expected: np.ndarray) -> None:
        self._output_layer._calculate_deltas_for_output_layer(expected)
        for i in range(self._size-2, 0, -1):
            delta = self._layers[i+1].delta @ self._layers[i+1].weight
            self._layers[i]._calculate_deltas_for_hidden_layer(delta)


    def _update(self) -> None:
        for i, layer in enumerate(self._layers[1:]):
            layer.weight += -np.outer(layer.delta, self._layers[i].output_cache) * layer.learning_rate 
            layer.bias += -layer.delta * layer.learning_rate

    
    def train(self, inputs: list[np.ndarray], expecteds: list[np.ndarray]) -> None:
        for _input, expected in zip(inputs, expecteds):
            self._outputs(_input)
            self._backpropagate(expected)
            self._update()


    def load_weights(self, weights: list[np.ndarray]) -> None:
        for layer, weight in zip(self._layers, weights):
            layer.weight = weight
    
    

