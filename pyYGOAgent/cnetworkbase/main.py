from .networkbase import cNetwork
import numpy as np

class Network(cNetwork):
    def __init__(self, layer_structure: list[int], learning_rate: float) -> None:
        super().__init__(layer_structure, learning_rate)

    
    def outputs(self, input_: np.ndarray) -> np.ndarray:
        return super().outputs(input_)

    
    def train(self, inputs: list[np.ndarray], expecteds: list[np.ndarray], epoch: int=1) -> None:
        super().trainForEpoch(inputs, expecteds, epoch)
