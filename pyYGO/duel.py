from typing import List, NamedTuple, Tuple

from pyYGO.field import HalfField
from pyYGO.card import Card
from pyYGO.zone import Zone
from pyYGO.enums import CardLocation, Phase, Player
from pyYGO.wrapper import Location, Position



class DuelField(NamedTuple):
    myside: HalfField
    opside: HalfField

    def set_zone_id(self) -> None:
        for i, zone in enumerate(self.myside.monster_zones):
            zone.id = Zone.ID.MZONE_0 << i
        for i, zone in enumerate(self.myside.spell_zones):
            zone.id = Zone.ID.SZONE_0 << i
        for i, zone in enumerate(self.opside.monster_zones):
            zone.id = Zone.ID.MZONE_0 << i << Zone.ID.OPPONENT
        for i, zone in enumerate(self.opside.spell_zones):
            zone.id = Zone.ID.SZONE_0 << i << Zone.ID.OPPONENT


class Duel:
    def __init__(self) -> None:
        self.field: DuelField = DuelField(HalfField(), HalfField())
        self.first: Player = None
        self.second: Player = None
        self.turn_player: Player = None
        self.turn: int = 0
        self.phase: Phase = None
        self.life: List[int] = [8000, 8000]

        self.mainphase_end: bool = False
        self.summoning: List[Card] = []
        self.last_summoned: List[Card] = []
        self.last_summon_player: Player = None

        self.current_chain: List[Card] = []
        self.last_chain_player: Player = -1
        self.chain_targets: List[Card] = []
        self.current_chain_target: List[Card] = []

        self.field.set_zone_id()


    @property
    def players(self) -> Tuple[Player]:
        return (self.first, self.second)


