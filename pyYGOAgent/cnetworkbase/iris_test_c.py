import csv
import time
from random import shuffle
from statistics import mean, stdev
from .main import Network
import numpy as np


def main() -> None:
    TIMES = 100
    EPOCH = 50
    LAYER_STRUCTURE = [4, 6, 3]
    LEARNING_RATE = 0.3

    with open('.\\iris.csv', mode='r') as f:
        dataset = list(csv.reader(f))
    iris_parameters, iris_classification, _ = read_dataset(dataset)

    train_time = []
    for _ in range(TIMES):
        network = Network(LAYER_STRUCTURE, LEARNING_RATE)
        t0 = time.time()
        network.trainForEpoch(iris_parameters[:140], iris_classification[:140], EPOCH)
        t1 = time.time()
        train_time.append((t1 - t0) * 1e3)
        correct_rate = validate(network, iris_parameters[140:], iris_classification[140:])
        #print(correct_rate*100, '%')
    print('mean:', mean(train_time), '[ms]')
    print('stdev:', stdev(train_time), '[ms]')
    


def read_dataset(dataset: list[list[str]]) -> tuple[list[np.ndarray], list[np.ndarray], list[str]]:
    irises: list[list[str]] = dataset
    classify: dict[str, np.ndarray[float]] = {
        'Iris-setosa':     np.array([1.0, 0.0, 0.0]),
        'Iris-versicolor': np.array([0.0, 1.0, 0.0]),
        'Iris-virginica':  np.array([0.0, 0.0, 1.0])
        }
    #シャッフルしてデータ加工
    shuffle(irises)
    iris_parameters: list[np.ndarray[float]] = [np.array(iris[0:4], dtype='float64') for iris in irises]
    iris_classification: list[np.ndarray[float]] = [classify[iris[4]] for iris in irises]
    iris_species: list[str] = [iris[4] for iris in irises]
 
    return normalize_by_feature_scaling(iris_parameters), iris_classification, iris_species


def normalize_by_feature_scaling(data: list[np.ndarray]) -> list[np.ndarray]:
    c = len(data[0])
    for i in range(c):
        arr = [d[i] for d in data]
        min_, max_ = min(arr), max(arr)
        for d in data:
            d[i] = (d[i] - min_) / (max_ - min_)
    return data



def validate(network: Network, inputs: list[np.ndarray], expecteds: list[np.ndarray]) -> float:
    correct: int = 0
    for input_, expected in zip(inputs, expecteds):
        result = network.outputs(input_)
        if result.argmax() == expected.argmax():
            correct += 1
    return correct / len(inputs)


def dump(percentages: list[float], folder_name: str, epoch: int, learning_rate: float, ):
    #学習結果ダンプ

    with open(f'.\\{folder_name}\\CorrectAnsRate_Epoch={epoch}_learningRate={np.floor(learning_rate*1000)/1000}.csv', mode='w') as f:
        f.write('max,'+str(max(percentages))+'%,')
        f.write('min,'+str(min(percentages))+'%,')
        f.write('mean,'+str(mean(percentages))+'%,')
        f.write('stdev,'+str(stdev(percentages))+'\n')
        f.write('%\n'.join([str(s) for s in percentages]))
        f.write('%')


if __name__ == '__main__':
    main()
    