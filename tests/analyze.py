from os import chdir
from pathlib import Path
import sys
import pandas
import numpy as np
import pylab as plt

chdir(Path(__file__).parent)

def init():
    path = sys.argv[1]
    try:
        df = pandas.read_csv(path)
    except:
        print('file not found: {}'.format(path))
        sys.exit()

    main(df)


def main(df: pandas.DataFrame):
    match_count = df['match'].values.astype('int')+1
    win = np.cumsum(df['win'].values.astype('int'))
    make_win_graph(match_count, win)
    make_winrate_graph(match_count, win)


def make_win_graph(match_count: np.ndarray, win: np.ndarray):
    fig = plt.figure()
    plt.plot(match_count, win)
    plt.xlabel('match count')
    plt.ylabel('win')
    plt.grid(True, which='both')
    plt.show()


def make_winrate_graph(match_count: np.ndarray, win:np.ndarray):
    fig = plt.figure()
    plt.plot(match_count, win/match_count * 100)
    plt.xlabel('match count')
    plt.ylabel('win rate [%]')
    plt.grid(True, which='both')
    plt.show()


if __name__ == '__main__':
    init()