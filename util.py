import argparse
from typing import NamedTuple


VERSION: int = 39 | 0<<8 | 9<<16 | 0<<24
class LaunchInfo(NamedTuple):
    name: str
    deck: str
    host: str
    port: int
    version: int
    notrain: bool


def load_args() -> LaunchInfo:
    parser = argparse.ArgumentParser()
    parser.set_defaults(name='AI', host='127.0.0.1', port=7911, version=VERSION, notrain=False)
    parser.add_argument('--name', type=str, help="AI's name (default: %(default)s)")
    parser.add_argument('--deck', type=str, help='deck name', required=True)
    parser.add_argument('--host', type=str, help='host adress (default: %(default)s)')
    parser.add_argument('--port', type=int, help='port (default: %(default)s)')
    parser.add_argument('--version', type=int, help='version (default: %(default)s)')
    parser.add_argument('--notrain', action='store_true', help='no train mode (default: %(default)s)')
    args: argparse.Namespace = parser.parse_args()
    return LaunchInfo(args.name, args.deck, args.host, args.port, args.version, args.notrain)


def error(message: str, exit_code: int=1) -> None:
    """ show message to user and close app """
    print(message)
    exit(exit_code)




if __name__ == '__main__':
    pass