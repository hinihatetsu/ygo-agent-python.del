import numpy as np
from typing import List
ndarray = List


def sigmoid(x: ndarray[float]) -> ndarray[float]:
    return 1 / (1 + np.exp(-x))

def derivative_sigmoid(x: ndarray[float]) -> ndarray[float]:
    sig = sigmoid(x)
    return sig * (1 - sig)


def linear(x: ndarray[float]) -> ndarray[float]:
    return x

def derivative_linear(x: ndarray[float]) -> float:
    return 1


def ReLU(x: ndarray[float]) -> ndarray[float]:
    return np.where(x < 0, 0, x).astype('float64')

def derivative_ReLU(x: float) -> float:
    return np.where(x < 0, 0, 1).astype('float64')


def softmax(x: ndarray[float]) -> ndarray[float]:
    sup = np.max(x)
    exp = np.exp(x - sup)
    total = np.sum(exp)
    return exp / total

def derivative_softmax(x: ndarray[float]) -> ndarray[float]:
    return 1


def tanh(x: ndarray[float]) -> ndarray[float]:
    return np.tanh(x)

def derivative_tanh(x: ndarray[float]) -> ndarray[float]:
    return 1 / (np.cosh(x))**2
 

def normalize_vector(vector: List[float]) -> List[float]:
    v: ndarray[float] = np.array(vector)
    norm: float = np.linalg.norm(v)
    return v / norm if norm != 0 else v

if __name__ == '__main__':
    pass

