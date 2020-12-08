#ifndef ACTIVATIONFUNCTIONS_HPP
#define ACTIVATIONFUNCTIONS_HPP
#define EIGEN_MPL2_ONLY
#include <Eigen/Core>

using namespace Eigen;

VectorXd tanh(const VectorXd &x);
VectorXd derTanh(const VectorXd &x);


inline VectorXd tanh(const VectorXd &x) {
    VectorXd res = x.array().tanh();
    return res;
}

inline VectorXd derTanh(const VectorXd &x) {
    VectorXd res = x.array().cosh().pow(2).inverse();
    return res;
}

#endif