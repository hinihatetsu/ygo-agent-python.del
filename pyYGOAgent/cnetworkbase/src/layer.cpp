#include "layer.hpp"
#include <cmath>
#include <iostream>

using namespace Eigen;
using std::cout;
using std::endl; 
using std::vector;

Layer::Layer(int numNeurons, int numInputs, double learningRate) {
    _learningRate = learningRate;
    _weight = MatrixXd::Random(numNeurons, numInputs).array() / sqrt(numInputs);
    _bias = VectorXd::Random(numNeurons).array() / sqrt(numNeurons);
    _delta = VectorXd::Zero(numNeurons);
    _inputCache = VectorXd::Zero(numNeurons);
    _outputCache = VectorXd::Zero(numNeurons);
    _activationFunc = tanh;
    _derivativeActivationFunc = derTanh;
    _isInputLayer = false;
    _isOutputLayer = false;
}

void Layer::setAsInputLayer() {
    _isInputLayer = true;
}

void Layer::setAsOutputLayer() {
    _isOutputLayer = true;
}

VectorXd Layer::outputCache() {
    return _outputCache;
}

void Layer::outputs(const VectorXd &input) {
    if (_isInputLayer) {
        _outputCache = input;
    } else {
        _inputCache = (_weight * input) + _bias;
        _outputCache = _activationFunc(_inputCache);
    }
}

VectorXd Layer::calcDelta(const VectorXd &x) {
    if (_isInputLayer) {
        return x;
    }
    if  (_isOutputLayer) {
        _delta = _derivativeActivationFunc(_inputCache).array() * (_outputCache - x).array();
    } else {
        _delta = _derivativeActivationFunc(_inputCache).array() * x.array();
    }
    return _delta.transpose() * _weight;
}

void Layer::update(const VectorXd &lastInput) {
    MatrixXd tmpM = (_delta * lastInput.transpose()).array() * _learningRate;
    VectorXd tmpV = _delta.array() * _learningRate;
    _weight -= tmpM;
    _bias -= tmpV;
}


void Layer::printStatus() {
    cout << "weight\n" << _weight << endl;
    cout << "\nbias\n" << _bias << endl;
}