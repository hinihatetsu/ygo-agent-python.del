#include "layer.hpp"
#include <cmath>
#include <iostream>
#include "translate.hpp"

using namespace Eigen;
using std::cout;
using std::endl; 
using std::vector;

Layer::Layer(int numNeurons, int numInputs, double learningRate, int activationFuncCode) {
    _learningRate = learningRate;
    _weight = MatrixXd::Random(numNeurons, numInputs).array() / sqrt(numInputs);
    _bias = VectorXd::Random(numNeurons).array() / sqrt(numNeurons);
    _delta = VectorXd::Zero(numNeurons);
    _inputCache = VectorXd::Zero(numNeurons);
    _outputCache = VectorXd::Zero(numNeurons);
    setActivationFunc(activationFuncCode);
    _isInputLayer = false;
    _isOutputLayer = false;
}


void Layer::setAsInputLayer() {
    _isInputLayer = true;
}


void Layer::setAsOutputLayer() {
    _isOutputLayer = true;
}


void Layer::setActivationFunc(int activationFuncCode) {
    switch (activationFuncCode) {
        case TANH:
            _activationFunc = tanh;
            _derivativeActivationFunc = derTanh;
            break;
        case SIGMOID:
            _activationFunc = sigmoid;
            _derivativeActivationFunc = derSigmoid;
            break;
        case LINEAR:
            _activationFunc = linear;
            _derivativeActivationFunc = derLinear;
            break;
        default:
            std::cout << "invalid activationFuncCode, Layer::setActivationFunc\n";
            exit(1);
    }
}


void Layer::setWeight(vector<double> &weight) {
    _weight = Map<MatrixXd>(&weight[0], _weight.rows(), _weight.cols()); 
}


void Layer::setBias(vector<double> &bias) {
    _bias = Map<VectorXd>(&bias[0], bias.size());
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


vector<double> Layer::getWeight() {
    auto r = _weight.rows(); 
    auto c = _weight.cols();
    vector<double> weight(r*c);
    Map<MatrixXd>(&weight[0], r, c) = _weight;
    return weight;
}


vector<double> Layer::getBias() {
    return toSTDVec(_bias);
}


void Layer::printStatus() {
    cout << "weight\n" << _weight << endl;
    cout << "\nbias\n" << _bias << endl;
}