#ifndef ACTIVATIONFUNCTIONS_HPP
#define ACTIVATIONFUNCTIONS_HPP
#define EIGEN_MPL2_ONLY
#include <Eigen/Core>

#define TANH    1
#define SIGMOID 2
#define LINEAR  3

using namespace Eigen;

VectorXd tanh(const VectorXd &x);
VectorXd derTanh(const VectorXd &x);
VectorXd sigmoid(const VectorXd &x);
VectorXd derSigmoid(const VectorXd &x);
VectorXd linear(const VectorXd &x);
VectorXd derLinear(const VectorXd &x);


inline VectorXd tanh(const VectorXd &x) {
    VectorXd res = x.array().tanh();
    return res;
}

inline VectorXd derTanh(const VectorXd &x) {
    VectorXd res = x.array().cosh().pow(2).inverse();
    return res;
}

inline VectorXd sigmoid(const VectorXd &x) {
    VectorXd res = (1 + (-x).array().exp()).inverse();
    return res;
}

inline VectorXd derSigmoid(const VectorXd &x) {
    VectorXd sig = sigmoid(x);
    VectorXd res = sig.array() * (1 - sig.array());
    return res;
}

inline VectorXd linear(const VectorXd &x) {
    return x;
}

inline VectorXd derLinear(const VectorXd &x) {
    return VectorXd::Ones(x.size());
}

#endif