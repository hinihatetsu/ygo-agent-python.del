#include "translate.hpp"


using namespace Eigen;

VectorXd toEigenVec(size_t vec_size, std::vector<double> &vec) {
    return Map<VectorXd>(&vec[0], vec_size);
}

std::vector<VectorXd> toEigenVecs(std::vector<std::vector<double>> &vecs) {
    size_t size = vecs.size();
    std::vector<VectorXd> res;
    if (size == 0) {
        return res;
    }
    size_t vec_size = vecs[0].size();
    res.reserve(size);
    for (size_t i = 0; i < size; ++i) {
        res.push_back(toEigenVec(vec_size, vecs[i]));
    }
    return res;
}

std::vector<double> toSTDVec(const VectorXd &vec) {
    size_t size = vec.size();
    std::vector<double> res(size, 0);
    Map<VectorXd>(&res[0], size) = vec;
    return res;
}
