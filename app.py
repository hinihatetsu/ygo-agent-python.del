import sys
from util import Config, LaunchInfo
from GameClient import GameClient


def main():
    launch_info: LaunchInfo = Config.load_args(sys.argv)
    client = GameClient(launch_info)
    client.start()


if __name__ == '__main__':
    main()
