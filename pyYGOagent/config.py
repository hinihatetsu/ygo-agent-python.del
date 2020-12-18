

class AgentConfig:
    def __init__(self, *, 
        max_match: int=500,
        epoch: int=20) -> None:

        self.max_match = max_match
        self.epoch = epoch