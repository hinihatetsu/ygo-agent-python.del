from libcpp.vector cimport vector
import numpy as np
cimport numpy as np
DTYPE = np.float64
ctypedef np.float64_t DTYPE_t

cdef extern from "network.hpp":
    cdef cppclass Network:
        Network(vector[int] layer_structure, double learningRate)
        vector[double] outputs(vector[double] input_)
        void trainForEpoch(vector[vector[double]] inputs, vector[vector[double]] expecteds, int epoch)


cdef class cNetwork:
    cdef Network* network
    def __init__(self, vector[int] layer_structure: list[int], double learning_rate: float) -> None:
        self.network = new Network(layer_structure, learning_rate)
    
    
    def __dealloc__(self):
        if self.network != NULL:
            del *self.network
    

    cpdef np.ndarray[DTYPE_t, ndim=1] outputs(self, np.ndarray[DTYPE_t, ndim=1] input_: np.ndarray):
        cdef vector[double] vin = input_
        cdef vector[double] x = self.network.outputs(vin)
        return np.asarray(x, dtype=DTYPE)


    cpdef trainForEpoch(self, vector[vector[double]] inputs: list[np.ndarray], vector[vector[double]] expecteds: list[np.ndarray], int epoch):
        self.network.trainForEpoch(inputs, expecteds, epoch)



