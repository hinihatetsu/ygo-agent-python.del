from typing import NoReturn

from pyYGO.enums import Player, CardPosition, CardType, Attribute, Race, Query
from pyYGO.wrapper import Location
from pyYGONetwork.packet import Packet


class Card:
    POSITION: dict[int, CardPosition] = {int(pos): pos for pos in CardPosition}
    ATTRIBUTE: dict[int, Attribute] = {int(a): a for a in Attribute}
    RASE: dict[int, Race] = {int(r): r for r in Race}
    def __init__(self, card_id: int=0, location: Location=None) -> NoReturn:
        # card info
        self.id: int = card_id
        self.arias: int = None
        self.type: list[CardType] = []
        self.level: int = None
        self.rank: int = None
        self.attribute: Attribute = None
        self.race: Race = None
        self.attack: int = None
        self.defence: int = None
        self.base_attack: int = None
        self.base_defence: int = None
        self.lscale: int = None
        self.rscale: int = None
        self.links: int = None
        self.linkmarker: int = None

        # status in duel
        self.controller: Player = None
        self.location: Location = location
        self.position: CardPosition = None
        self.target_cards: list[Card] = []
        self.targeted_by: list[Card] = []
        self.equip_target: Card = None
        self.equip_cards: list[Card] = []
        self.overlays: list[int] = []

        # status flag
        self.attacked: bool = False
        self.disabled: bool = False
        self.proc_complete: bool = False
        self.can_direct_attack: bool = False
        self.is_special_summoned: bool = False
        self.is_faceup: bool = False

    
    @property
    def is_attack(self) -> bool:
        return bool(self.position & CardPosition.ATTACK)

    @property
    def is_defence(self) -> bool:
        return bool(self.position & CardPosition.DEFENCE)


    def update(self, packet: Packet) -> NoReturn:
        while True:
            size: int = packet.read_int(2)
            if size == 0:
                return

            query: int = packet.read_int(4)
            if query == Query.ID:
                self.id = packet.read_int(4)
    
            elif query == Query.POSITION:
                pos = packet.read_int(4)
                self.position = self.POSITION[pos] if pos in self.POSITION else pos

            elif query == Query.ALIAS:
                self.arias = packet.read_int(4)

            elif query == Query.TYPE:
                type_ = packet.read_int(4)
                self.type.clear()
                for t in CardType:
                    if type_ & t:
                        self.type.append(t)

            elif query == Query.LEVEL:
                self.level = packet.read_int(4)

            elif query == Query.RANK:
                self.rank = packet.read_int(4)

            elif query == Query.ATTRIBUTE:
                attr = packet.read_int(4)
                self.atrribute = self.ATTRIBUTE[attr] if attr in self.ATTRIBUTE else attr

            elif query == Query.RACE:
                race = packet.read_int(4)
                self.race = self.RASE[race] if race in self.RASE else race 

            elif query == Query.ATTACK:
                self.attack = packet.read_int(4)

            elif query == Query.DEFENCE:
                self.defence = packet.read_int(4)

            elif query == Query.BASE_ATTACK:
                self.base_attack = packet.read_int(4)

            elif query == Query.BASE_DEFENCE:
                self.base_defence = packet.read_int(4)

            elif query == Query.OVERLAY_CARD:
                num_of_overlay: int = packet.read_int(4)
                self.overlays: list[int] = [packet.read_int(4) for _ in range(num_of_overlay)]

            elif query == Query.CONTROLLER:
                self.controller = packet.read_player()

            elif query == Query.STATUS:
                DISABLED = 0x0001
                PROC_COMPLETE = 0x0008
                status: int = packet.read_int(4)
                self.disabled = bool(status & DISABLED)
                self.proc_complete = bool(status & PROC_COMPLETE)

            elif query == Query.LSCALE:
                self.lscale = packet.read_int(4)

            elif query == Query.RSCALE:
                self.rscale = packet.read_int(4)

            elif query == Query.LINK:
                self.links = packet.read_int(4)
                self.linkmarker = packet.read_int(4)

            elif query == Query.END:
                return

            else:
                packet.read_bytes(size - 4) # 4 is bytesize of 'query'


    def __repr__(self) -> str:
        return f'<{self.id}>'


        