#ifndef LAYER_HPP
#define LAYER_HPP

#include <vector>
#define EIGEN_MPL2_ONLY
#include <Eigen/Core>
#include "activationFunctions.hpp"

using std::vector;
using namespace Eigen;

class Layer {
    public:
        Layer(int numNeurons, int numInputs, double learningRate);
        void setAsInputLayer();
        void setAsOutputLayer();
        VectorXd outputCache();
        void outputs(const VectorXd &input);
        VectorXd calcDelta(const VectorXd &x);
        void update(const VectorXd &lastInput);
        vector<double> getWeight();
        vector<double> getBias();
        void setWeight(vector<double> &weight);
        void setBias(vector<double> &bias);
        void printStatus();  
    
    private:
        double _learningRate;
        MatrixXd _weight;
        VectorXd _bias;
        VectorXd _delta;
        VectorXd _inputCache;
        VectorXd _outputCache;
        VectorXd (*_activationFunc)(const VectorXd &x);
        VectorXd (*_derivativeActivationFunc)(const VectorXd &x);
        bool _isInputLayer;
        bool _isOutputLayer;
};



#endif