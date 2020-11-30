#ifndef TRANSLATE_HPP
#define TRANSLATE_HPP
#define EIGEN_MPL2_ONLY
#include <Eigen/Core>
#include <vector>

using namespace Eigen;

VectorXd toEigenVec(size_t vec_size, std::vector<double> &vec);

std::vector<VectorXd> toEigenVecs(std::vector<std::vector<double>> &vecs);

std::vector<double> toSTDVec(const VectorXd &vec);



#endif