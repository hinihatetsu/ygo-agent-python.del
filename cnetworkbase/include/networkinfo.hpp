#ifndef NETWORKINFO_HPP
#define NETWORKINFO_HPP

#include <vector>
using std::vector;

class NetworkInfo {
    public:
        NetworkInfo();
        vector<vector<double>> weights;
        vector<vector<double>> biases;
};

#endif // NETWORKINFO_H