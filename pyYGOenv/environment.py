

import numpy as np
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step as ts


from pyYGOenv.executor import EnvGameExecutor
from pyYGOclient.client import GameClient


class YGOEnv(py_environment.PyEnvironment):
    def __init__(self, deck_name: str, host: str, port: int, version: int, name: str) -> None:
        client: GameClient = GameClient(deck_name, host, port, version, name)
        self._executor: EnvGameExecutor = EnvGameExecutor(client)
        # env parameters
        self._action_spec = array_spec.BoundedArraySpec(shape=(), dtype=np.float32, minimum=-1, maximum=1, name='action')
        self._observation_spec = array_spec.BoundedArraySpec(shape=self._executor.state_shape, dtype=np.float32, name='observation')
        self._episode_ended: bool = False
    

    def action_spec(self) -> array_spec.ArraySpec:
        return self._action_spec

    
    def observation_spec(self) -> array_spec.ArraySpec:
        return self._observation_spec


    def _reset(self) -> ts.TimeStep:
        state = self._executor.get_state()
        self._episode_ended = False
        return ts.restart(state)


    def _step(self, action: np.ndarray):
        if self._episode_ended:
            return self.reset()

        should_execute = True if action >= 0 else False
        self._executor.execute(should_execute)

        state = self._executor.get_state()
        self._episode_ended = self._executor.game_ended()
        reward = self._executor.get_reward()

        if self._episode_ended:
            return ts.termination(state, reward)
        else:
            return ts.transition(state, reward=0.0, discount=1.0)

    
    def close(self) -> None:
        self._executor.close()
        




