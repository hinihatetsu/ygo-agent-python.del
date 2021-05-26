from util import LaunchInfo, load_args
from .environment import YGOEnvironment
from .agent import DuelAgent


def main():
    info: LaunchInfo = load_args()
    collect_env = YGOEnvironment(info.deck, info.host, info.port, info.version, info.name+'_collect')
    eval_env = YGOEnvironment(info.deck, info.host, info.port+1, info.version, info.name+'_eval')
    agent = DuelAgent(collect_env, eval_env)
    agent.train(10000)
    collect_env.close()
    eval_env.close()


if __name__ == '__main__':
    main()
