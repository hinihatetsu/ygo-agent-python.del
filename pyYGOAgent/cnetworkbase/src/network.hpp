#ifndef NETWORK_HPP
#define NETWORK_HPP

#include <vector>
#define EIGEN_MPL2_ONLY
#include <Eigen/Core>
#include "layer.hpp"


using std::vector;
using namespace Eigen;

class Network {
    public:
        Network(vector<int> layerStructure, double learningRate);
        vector<double> outputs(vector<double> &input);
        void trainForEpoch(vector<vector<double>> &inputs, vector<vector<double>> &outputs, int epoch);
        void printStatus();

    private:
        VectorXd _outputs(const VectorXd &input);
        void _train(size_t inputs_size, const vector<VectorXd> &inputs, const vector<VectorXd> &outputs);
        void _update(const VectorXd &expected);
        int _size;
        vector<int> _layerStructure;
        vector<Layer> _layers;
};



#endif