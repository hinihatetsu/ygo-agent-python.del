from typing import List

from .enums import Player
from .cardstatus import Location, Type, Attribute, Race, Position


class Card:
    def __init__(self, card_id: int=0, location: Location=Location(0)) -> None:
        # card info
        self.id: int = card_id
        self.arias: int = 0
        self.type: Type = Type(0)
        self.level: int = 0
        self.rank: int = 0
        self.attribute: Attribute = Attribute(0)
        self.race: Race = Race(0)
        self.attack: int = 0
        self.defence: int = 0
        self.base_attack: int = 0
        self.base_defence: int = 0
        self.lscale: int = 0
        self.rscale: int = 0
        self.link: int = 0
        self.linkmarker: int = 0

        # status in duel
        self.controller: Player = Player.NONE
        self.location: Location = location
        self.position: Position = Position(0)
        self.target_cards: List[Card] = []
        self.targeted_by: List[Card] = []
        self.equip_target: Card = None
        self.equip_cards: List[Card] = []
        self.overlays: List[int] = []
        self.reason: int = 0
        self.reason_card: Card = None
        self.counters: dict[int, int] = dict()

        # status flag
        self.status: int = 0
        self.attacked: bool = False
        self.can_direct_attack: bool = False
        self.is_special_summoned: bool = False
        self.is_faceup: bool = False

    
    def is_attack(self) -> bool:
        return self.position.is_attack()


    def is_defence(self) -> bool:
        return self.position.is_defence()


    def __repr__(self) -> str:
        return f'<{self.id}>'


        