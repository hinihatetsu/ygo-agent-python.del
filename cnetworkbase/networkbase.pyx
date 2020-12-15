from libcpp.vector cimport vector
import numpy as np
cimport numpy as np

DTYPE = np.float64
ctypedef np.float64_t DTYPE_t

cdef extern from "network.hpp":
    cdef cppclass Network:
        Network(const vector[int] &layer_structure, double learningRate, vector[int] activationFuncCodes)
        vector[double] outputs(vector[double] input_)
        void trainForEpoch(vector[vector[double]] inputs, vector[vector[double]] expecteds, int epoch)
        NetworkInfo* dump()
        void load(NetworkInfo* info)


cdef extern from "networkinfo.hpp":
    cdef cppclass NetworkInfo:
        vector[vector[double]] weights
        vector[vector[double]] biases


cdef class cNetwork:
    cdef Network* network

    def __init__(self, layer_structure: list[int], learning_rate: float, activation_func_codes: list[int]) -> None:
        self._layer_structure: list[int] = layer_structure
        self._learning_rate: float = learning_rate
        self._activation_func_codes: list[int] = activation_func_codes
        self.network = new Network(layer_structure, learning_rate, activation_func_codes)
    

    def __dealloc__(self):
        del self.network
    
    
    cpdef np.ndarray[DTYPE_t, ndim=1] outputs(self, vector[double] input_: np.ndarray):
        cdef vector[double] x = self.network.outputs(input_)
        return np.asarray(x, dtype=DTYPE)


    def trainForEpoch(self, vector[vector[double]] inputs: list[np.ndarray], vector[vector[double]] expecteds: list[np.ndarray], int epoch):
        self.network.trainForEpoch(inputs, expecteds, epoch)


    def __getstate__(self):
        cdef NetworkInfo* info = self.network.dump()
        self.weights = info.weights
        self.biases = info.biases
        del info
        state = self.__dict__.copy()
        del self.weights
        del self.biases
        return state


    def __setstate__(self, state):
        self.__dict__.update(state)
        self.network = new Network(self._layer_structure, self._learning_rate, self._activation_func_codes)
        cdef NetworkInfo* info = new NetworkInfo()
        info.weights = self.weights
        info.biases = self.biases
        self.network.load(info)
        del self.weights
        del self.biases
        del info


    
    

