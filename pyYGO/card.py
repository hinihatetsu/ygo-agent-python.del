from .enums import Player, CardPosition, CardType, Attribute, Race
from .wrapper import Location


class Card:
    POSITION: dict[int, CardPosition] = {int(pos): pos for pos in CardPosition}
    ATTRIBUTE: dict[int, Attribute] = {int(a): a for a in Attribute}
    RASE: dict[int, Race] = {int(r): r for r in Race}
    def __init__(self, card_id: int=0, location: Location=None) -> None:
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


    def __repr__(self) -> str:
        return f'<{self.id}>'


        