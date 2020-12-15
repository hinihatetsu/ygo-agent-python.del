#ifndef NETWORK_HPP
#define NETWORK_HPP

#include <vector>
#define EIGEN_MPL2_ONLY
#include <Eigen/Core>
#include "layer.hpp"
#include "networkinfo.hpp"


using std::vector;
using namespace Eigen;

class Network {
    public:
        Network(const vector<int> &layerStructure, double learningRate);
        vector<double> outputs(vector<double> &input);
        void trainForEpoch(vector<vector<double>> &inputs, vector<vector<double>> &outputs, int epoch);
        NetworkInfo* dump();
        void load(NetworkInfo* info);
        void printStatus();

    private:
        void _outputs(const VectorXd &input);
        void _train(size_t inputs_size, const vector<VectorXd> &inputs, const vector<VectorXd> &outputs);
        void _update(const VectorXd &expected);
        int _size;
        vector<int> _layerStructure;
        vector<Layer> _layers;
};



#endif