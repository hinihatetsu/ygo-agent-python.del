import numpy as np
from typing import List

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))

def derivative_sigmoid(x: np.ndarray) -> np.ndarray:
    sig = sigmoid(x)
    return sig * (1 - sig)


def linear(x: np.ndarray) -> np.ndarray:
    return x

def derivative_linear(x: np.ndarray) -> np.ndarray:
    return np.ones(x.shape)


def ReLU(x: np.ndarray) -> np.ndarray:
    return np.where(x < 0, 0, x)

def derivative_ReLU(x: np.ndarray) -> np.ndarray:
    return np.where(x < 0, 0, 1)


def softmax(x: np.ndarray) -> np.ndarray:
    sup = np.max(x)
    exp = np.exp(x - sup)
    total = np.sum(exp)
    return exp / total

def derivative_softmax(x: np.ndarray) -> np.ndarray:
    return np.ones(x.shape)


def tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)

def derivative_tanh(x: np.ndarray) -> np.ndarray:
    return 1 / (np.cosh(x))**2
 

def normalize_vector(vector: List[float]) -> List[float]:
    v: np.ndarray[float] = np.array(vector)
    norm: float = np.linalg.norm(v)
    return v / norm if norm != 0 else v

if __name__ == '__main__':
    pass

