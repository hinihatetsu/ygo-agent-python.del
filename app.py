import sys
from typing import NamedTuple, Dict, List, Any
from util import LaunchInfo, load_args
from GameClient import GameClient


def main():
    launch_info: LaunchInfo = load_args(sys.argv)
    client = GameClient(launch_info)
    client.start()


if __name__ == '__main__':
    main()
