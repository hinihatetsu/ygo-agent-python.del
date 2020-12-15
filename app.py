from util import LaunchInfo, load_args
from pyYGOenvironment import GameClient
from pyYGOagent import DuelAgent


def main():
    info: LaunchInfo = load_args()
    agent = DuelAgent(info.deck, info.notrain)
    client = GameClient(info.host, info.port, info.version, info.name)
    agent.set_client(client)
    agent.run()


if __name__ == '__main__':
    main()
