from typing import Dict, List

from pyYGO.card import Card
from pyYGO.zone import Zone, MonsterZone, SpellZone
from pyYGO.enums import CardLocation, CardType



class HalfField(Dict[CardLocation, List]):
    def __init__(self) -> None:
        self.hand: List[Card] = []
        self.deck: List[Card] = []
        self.extradeck: List[Card] = []
        self.graveyard: List[Card] = []
        self.banished: List[Card] = []
        # left first
        self.monster_zones: List[MonsterZone] = [MonsterZone() for _ in range(7)]
        self.mainmonster_zones: List[MonsterZone] = self.monster_zones[0:5]
        self.exmonster_zones: List[MonsterZone] = self.monster_zones[5:7]
        self.spell_zones: List[SpellZone] = [SpellZone() for _ in range(6)]
        self.Fspell_zone: SpellZone = self.spell_zones[5]
        self.pendulum_zones: List[SpellZone] = [self.spell_zones[0], self.spell_zones[4]]

        self[CardLocation.HAND] = self.hand
        self[CardLocation.DECK] = self.deck
        self[CardLocation.EXTRADECK] = self.extradeck
        self[CardLocation.GRAVE] = self.graveyard
        self[CardLocation.BANISHED] = self.banished
        self[CardLocation.MONSTER_ZONE] = self.monster_zones
        self[CardLocation.SPELL_ZONE] = self.spell_zones
        self[CardLocation.FSPELL_ZONE] = self.Fspell_zone
        self[CardLocation.PENDULUM_ZONE] = self.pendulum_zones
        
        self.battling_monster: Card = None
        self.under_attack: bool = False


    @property
    def exzonemonster_count(self) -> int:
        return sum(int(zone.has_card) for zone in self.exmonster_zones)

    @property
    def monster_count(self) -> int:
        return sum(int(zone.has_card) for zone in self.monster_zones)

    @property
    def spell_without_Fspell_count(self) -> int:
        return sum(int(zone.has_card) for zone in self.spell_zones[0:5])

    @property
    def spell_count(self) -> int:
        return sum(int(zone.has_card) for zone in self.spell_zones)

    @property
    def hand_count(self) -> int:
        return len(self.hand)

    @property
    def deck_count(self) -> int:
        return len(self.deck)

    @property
    def columncard_count(self, column: int, include_exzone: bool=True) -> None:
        column_zones: Dict[int, List[Zone]] = {

            0: [self.spell_zones[0], self.mainmonster_zones[0]],
            1: [self.spell_zones[1], self.mainmonster_zones[1], self.exmonster_zones[0]] if include_exzone else  [self.spell_zones[1], self.mainmonster_zones[1]],
            2: [self.spell_zones[2], self.mainmonster_zones[2]],
            3: [self.spell_zones[3], self.mainmonster_zones[3], self.exmonster_zones[1]] if include_exzone else [self.spell_zones[3], self.mainmonster_zones[3]],
            4: [self.spell_zones[4], self.mainmonster_zones[4]]
        }
        return sum(int(zone.has_card for zone in column_zones[column]))

    @property
    def field_count(self) -> int:
        return self.monster_count + self.spell_count

    @property
    def fieldhand_count(self) -> int:
        return self.field_count + self.hand_count

    @property
    def is_field_empty(self) -> bool:
        return self.field_count == 0


    def set_deck(self, num_of_main: int, num_of_extra: int) -> None:
        self.deck = [Card() for _ in range(num_of_main)]
        self.extradeck = [Card() for _ in range(num_of_extra)]
        self[CardLocation.DECK] = self.deck
        self[CardLocation.EXTRADECK] = self.extradeck


    def get_mainzone_monsters(self) -> List[Card]:
        return [zone.card for zone in self.mainmonster_zones if zone.has_card]


    def get_exzone_monsters(self) -> List[Card]:
        return [zone.card for zone in self.exmonster_zones if zone.has_card]
    

    def get_monsters(self) -> List[Card]:
        return [zone.card for zone in self.monster_zones if zone.has_card]

    
    def get_graveyard_monsters(self) -> List[Card]:
        return [card for card in self.graveyard if card.type == CardType.MONSTER]


    def get_graveyard_spells(self) -> List[Card]:
        return [card for card in self.graveyard if card.type == CardType.SPELL]
    
    
    def get_graveyard_traps(self) -> List[Card]:
        return [card for card in self.graveyard if card.type == CardType.TRAP]

    
    def get_spells(self) -> List[Card]:
        return [zone.card for zone in self.spell_zones if zone.has_card]
        

    def get_Fspell(self) -> Card:
        return self.Fspell_zone.card

    
    def contains_in_hand(self, card_id: int) -> bool:
        return card_id in [card.id for card in self.hand]

    
    def contains_in_graveyard(self, card_id: int) -> bool:
        return card_id in [card.id for card in  self.graveyard]


    def contains_in_banished(self, card_id: int) -> bool:
        return card_id in [card.id for card in self.graveyard]


    def contains_in_extradeck(self, card_id: int) -> bool:
        return card_id in [card.id for card in self.extradeck]


    def has_attak_monster(self) -> bool:
        return any(zone.card.is_attack for zone in self.monster_zones) 

    
    def has_defence_monster(self) -> bool:
        return any(zone.card.is_defence for zone in self.monster_zones)


