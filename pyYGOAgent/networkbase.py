from functools import reduce
from typing import List, Callable, TypeVar
from pyYGOAgent.util import liner, derivative_liner, sigmoid, derivative_sigmoid, ReLU, derivative_ReLU, softmax, derivative_softmax, tanh, derivative_tanh
import numpy as np
ndarray = TypeVar('ndarray')

der_act_funcs = {sigmoid: derivative_sigmoid,
                 liner: derivative_liner,
                 ReLU: derivative_ReLU,
                 softmax: derivative_softmax,
                 tanh: derivative_tanh}

class Layer:
    def __init__(self, prev_layer, num_neurons: int, learning_rate: float, act_func: Callable[[float], float]) -> None:
        self.prev_layer: Layer = prev_layer
        self.num_neurons: int = num_neurons
        self.learning_rate: float = learning_rate
         
        num_inputs: int = num_neurons if self.prev_layer is None else self.prev_layer.num_neurons
        self.weight: ndarray[float] = np.random.rand(num_neurons, num_inputs) / np.sqrt(num_inputs)
        self.bias: ndarray[float] = np.random.rand(num_neurons)
        self.delta: ndarray[float] = np.zeros(num_neurons, dtype='float64')
        self.input_cache: ndarray[float] = np.zeros(num_neurons)
        self.output_cache: ndarray[float] = np.zeros(num_neurons)
        self.activation_func: Callable[[float], float] = act_func
        self.derivative_activation_func: Callable[[float], float] = der_act_funcs[act_func]


    def outputs(self, inputs: ndarray) -> ndarray:    
        if self.prev_layer is None:
            self.input_cache = inputs
            self.output_cache = inputs
        else:
            self.input_cache = self.weight @ inputs + self.bias
            self.output_cache = self.activation_func(self.input_cache)
        return self.output_cache



class Network:
    def __init__(self, layer_structure: List[int], learning_rate: float=0.01, act_func: Callable[[float], float]=tanh) -> None:      
        self._layer_structure: List[int] = layer_structure
        self._layers: List[Layer] = [Layer(None, layer_structure[0], learning_rate, act_func)]
        self.learning_rate: float = learning_rate
        self._layer_size: int = len(self._layer_structure)
        for prev, n in enumerate(layer_structure[1:]):
            self._layers += [Layer(self._layers[prev], n, learning_rate, act_func)]
        self._output_layer: Layer = self._layers[self._layer_size-1]
        
    @property
    def _layers_weights(self) -> List[ndarray]:
        return [layer.weight for layer in self._layers]


    def _outputs(self, inputs: ndarray) -> ndarray:
        inputs = np.array(inputs)
        activate = lambda inputs, layer: layer.outputs(inputs)
        return reduce(activate, self._layers, inputs)


    def _calculate_deltas_for_output_layer(self, expected: ndarray, num_of_batch: int) -> None:
        layer: Layer = self._output_layer
        layer.delta = layer.derivative_activation_func(layer.input_cache) * (expected - layer.output_cache) / num_of_batch


    def _calculate_deltas_for_hidden_layer(self, layer: Layer, next_layer: Layer) -> None:
        layer.delta = layer.derivative_activation_func(layer.input_cache) * (next_layer.delta @ next_layer.weight)


    def _backpropagate(self, expected: ndarray, num_of_batch: int=1) -> None:
        self._calculate_deltas_for_output_layer(expected, num_of_batch)
        for i in range(self._layer_size-2, 0, -1):
            self._calculate_deltas_for_hidden_layer(self._layers[i], self._layers[i+1])


    def _update(self) -> None:
        for layer in self._layers[1:]:
            layer.weight += layer.delta.reshape((layer.num_neurons,1)) * layer.prev_layer.output_cache * layer.learning_rate
            layer.bias += layer.delta * layer.learning_rate

    
    def train(self, inputs: List[ndarray], expecteds: List[ndarray]) -> None:
        for _input, expected in zip(inputs, expecteds):
            self._outputs(_input)
            self._backpropagate(expected)
            self._update()


    def validate(self, inputs: List[ndarray], expecteds: List[ndarray]) -> float:
        correct: int = 0
        for _input, expected in zip(inputs, expecteds):
            result: ndarray[float] = self._outputs(_input)
            if result.argmax() == expected.argmax():
                correct += 1
        return correct / len(inputs)


    def load_weights(self, weights: List[ndarray]) -> None:
        for layer, weight in zip(self._layers, weights):
            layer.weight = weight
    
    
