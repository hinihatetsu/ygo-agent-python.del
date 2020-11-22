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
    def __init__(self, prev_layer, num_neurons: int, learning_rate: float, act_func: Callable[[np.ndarray], np.ndarray]) -> None:
        self.prev_layer: Layer = prev_layer
        self.num_neurons: int = num_neurons
        self.learning_rate: float = learning_rate
         
        num_inputs: int = num_neurons if self.prev_layer is None else self.prev_layer.num_neurons
        self.weight: np.ndarray[float] = np.random.randn(num_neurons, num_inputs) / np.sqrt(num_inputs)
        self.bias: np.ndarray[float] = np.random.randn(num_neurons) / np.sqrt(num_neurons)
        self.delta: np.ndarray[float] = np.zeros(num_neurons, dtype='float64')
        self.input_cache: np.ndarray[float] = np.zeros(num_neurons)
        self.output_cache: np.ndarray[float] = np.zeros(num_neurons)
        self.activation_func = act_func


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
        if self.prev_layer is None:
            self.input_cache = inputs
            self.output_cache = inputs
        else:
            self.input_cache = self.weight @ inputs + self.bias
            self.output_cache = self.activation_func(self.input_cache)
        return self.output_cache



class Network:
    def __init__(self, layer_structure: list[int], learning_rate: float=0.01, act_func: Callable[[np.ndarray], np.ndarray]=tanh) -> None:      
        self._layer_structure: list[int] = layer_structure
        self._layers: list[Layer] = [Layer(None, layer_structure[0], learning_rate, act_func)]
        self.learning_rate: float = learning_rate
        self._layer_size: int = len(self._layer_structure)
        for prev, n in enumerate(layer_structure[1:]):
            self._layers.append(Layer(self._layers[prev], n, learning_rate, act_func))
        self._output_layer: Layer = self._layers[self._layer_size-1]
        
    @property
    def _layers_weights(self) -> list[np.ndarray]:
        return [layer.weight for layer in self._layers]


    def _activate(self, inputs: np.ndarray, layer: Layer) -> np.ndarray:
        return layer.outputs(inputs)


    def _outputs(self, inputs: np.ndarray) -> np.ndarray:
        return reduce(self._activate, self._layers, inputs)


    def _calculate_deltas_for_output_layer(self, expected: np.ndarray) -> None:
        layer: Layer = self._output_layer
        layer.delta = layer.derivative_activation_func(layer.input_cache) * (layer.output_cache - expected) 


    def _calculate_deltas_for_hidden_layer(self, layer: Layer, next_layer: Layer) -> None:
        layer.delta = layer.derivative_activation_func(layer.input_cache) * (next_layer.delta @ next_layer.weight)


    def _backpropagate(self, expected: np.ndarray) -> None:
        self._calculate_deltas_for_output_layer(expected)
        for i in range(self._layer_size-2, 0, -1):
            self._calculate_deltas_for_hidden_layer(self._layers[i], self._layers[i+1])


    def _update(self) -> None:
        for layer in self._layers[1:]:
            layer.weight += -np.outer(layer.delta, layer.prev_layer.output_cache) * layer.learning_rate
            layer.bias += -layer.delta * layer.learning_rate

    
    def train(self, inputs: list[np.ndarray], expecteds: list[np.ndarray]) -> None:
        for _input, expected in zip(inputs, expecteds):
            self._outputs(_input)
            self._backpropagate(expected)
            self._update()


    def load_weights(self, weights: list[np.ndarray]) -> None:
        for layer, weight in zip(self._layers, weights):
            layer.weight = weight
    
    

