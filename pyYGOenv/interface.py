
import numpy as np

from pyYGOclient.client import GameClient
from .executor import EnvGameExecutor

class ClientInterface:
    """ 
    Client interface for pyYGOenvironment.YGOEnv

    Attributes
    ----------
    state_shape : tuple of int
        Shape of state array.

    Methods
    -------
    get_state() : np.ndarray
        Return state array of the current game.

    execute(should_execute: bool)
        Execute action.

    game_ended() : bool
        Return True if the current game has ended.

    get_reward() : float
        Return reward of match result.

    close()
        Free any resouses used by the client.
    """
    def __init__(self, deck_name: str, host: str, port: int, version: int, name: str) -> None:
        client: GameClient = GameClient(deck_name, host, port, version, name)
        self._executor: EnvGameExecutor = EnvGameExecutor(client)
        self._executor.run()


    @property
    def state_shape(self) -> tuple:
        return self._executor.state_shape


    def get_state(self) -> np.ndarray:
        return self._executor.get_state()


    def execute(self, should_execute: bool) -> None:
        self._executor.execute(should_execute)


    def game_ended(self) -> bool:
        return self._executor.game_ended()


    def get_reward(self) -> float:
        return self._executor.get_reward()


    def close(self) -> None:
        self._executor.close()

