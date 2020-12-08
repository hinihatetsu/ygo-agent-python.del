import argparse
from argparse import Namespace
from typing import NamedTuple


VERSION: int = 38 | 1<<8 | 8<<16
class LaunchInfo(NamedTuple):
    name: str
    deck: str
    host: str
    port: int
    version: int


def load_args() -> LaunchInfo:
    parser = argparse.ArgumentParser()
    parser.set_defaults(name='AI', host='127.0.0.1', port=7911, version=VERSION)
    parser.add_argument('--name', type=str, help="AI's name (default: %(default)s)")
    parser.add_argument('--deck', type=str, help='deck name', required=True)
    parser.add_argument('--host', type=str, help='host adress (default: %(default)s)')
    parser.add_argument('--port', type=int, help='port (default: %(default)s)')
    parser.add_argument('--version', type=int, help='version (default: %(default)s)')
    args: Namespace = parser.parse_args()
    return LaunchInfo(args.name, args.deck, args.host, args.port, args.version)


def error(message: str, exit_code: int=1) -> None:
    """ show message to user and close app"""
    print(message)
    exit(exit_code)




if __name__ == '__main__':
    pass