import sys
from typing import NamedTuple, Dict, List, Any
from GameClient import GameClient


class LaunchInfo(NamedTuple):
    name: str = 'AI'
    deck: str = ''
    host: str = '127.0.0.1'
    port: int = 7911
    version: int = 38 | 1<<8 | 8<<16


def main():
    launch_info: LaunchInfo = load_args(sys.argv)
    client = GameClient(launch_info)
    client.start()


def load_args(args: List[str]) -> LaunchInfo:
    info: Dict[str, Any] = dict()
    for arg in args:
        equal_index: int = arg.find('=')
        if equal_index == (-1 or len(arg)-1):
            continue

        key: str = arg[:equal_index].lower()
        if key in {'name', 'deck', 'host'}:
            info[key] = arg[equal_index+1:]
        elif key in {'port', 'version'}:
            info[key] = int(arg[equal_index+1:])
    
    return LaunchInfo(**info)


if __name__ == '__main__':
    main()
