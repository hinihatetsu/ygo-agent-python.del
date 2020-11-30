from .wrapper import Location
from .card import Card
from .zone import Zone, MonsterZone, SpellZone
from .enums import CardLocation, CardType



class HalfField():
    def __init__(self) -> None:
        self.hand: list[Card] = []
        self.deck: list[Card] = []
        self.extradeck: list[Card] = []
        self.graveyard: list[Card] = []
        self.banished: list[Card] = []
        # left first
        self.monster_zones: list[MonsterZone] = [MonsterZone() for _ in range(7)]
        self.spell_zones: list[SpellZone] = [SpellZone() for _ in range(6)]
        
        self.battling_monster: Card = None
        self.under_attack: bool = False
    
    @property
    def mainmonster_zones(self) -> list[MonsterZone]:
        return self.monster_zones[0:5]

    @property
    def exmonster_zones(self) -> list[MonsterZone]:
        return self.monster_zones[5:7]

    @property
    def Fspell_zone(self) -> SpellZone:
        return self.spell_zones[5]

    @property
    def pendulum_zones(self) -> list[SpellZone]:
        return [self.spell_zones[0], self.spell_zones[4]]

    @property
    def column_zones(self) -> list[list[Zone]]:
        return [
            [self.spell_zones[0], self.mainmonster_zones[0]],
            [self.spell_zones[1], self.mainmonster_zones[1], self.exmonster_zones[0]],
            [self.spell_zones[2], self.mainmonster_zones[2]],
            [self.spell_zones[3], self.mainmonster_zones[3], self.exmonster_zones[1]],
            [self.spell_zones[4], self.mainmonster_zones[4]]
        ]

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
    def columncard_count(self, column: int) -> None:
        return sum(int(zone.has_card) for zone in self.column_zones[column])

    @property
    def field_count(self) -> int:
        return self.monster_count + self.spell_count

    @property
    def fieldhand_count(self) -> int:
        return self.field_count + self.hand_count

    @property
    def is_field_empty(self) -> bool:
        return self.field_count == 0

    
    def get_card(self, location: Location, index: int) -> Card:
        if location.is_overlay:
            return Card(location=location)

        where: list = self.where(location)
        card: Card = Card()

        if where is None:
            return card
        
        if location.is_zone:
            zone: Zone = where[index]
            card: Card = zone.card        
        else:
            card: Card = where[index]

        return card

    
    def add_card(self, card: Card, location: Location, index: int) -> None:
        where: list = self.where(location)
        if where is None:
            del card
            return

        if location.is_overlay:
            if location.is_zone:
                zone: Zone = where[index]
                zone.card.overlays.append(card.id)
            else:
                pcard: Card = where[index]
                pcard.overlays.append(card.id)
            return
        
        if location.is_zone:
            zone: Zone = where[index]
            zone.card = card
        else:
            where.insert(index, card)

    
    def remove_card(self, card: Card, location: Location, index: int) -> None:
        where: list = self.where(location)
        if where is None:
            return
        
        if location.is_overlay:
            if location.is_zone:
                zone: Zone = where[index]
                zone.card.overlays.remove(card.id)
            else:
                pcard: Card = where[index]
                pcard.overlays.remove(card.id)
            return
        
        if location.is_zone:
            zone: Zone = where[index]
            zone.card = None
        else:
            where.remove(card)


    def where(self, location: Location) -> list:
        if location & CardLocation.DECK:
            return self.deck

        elif location & CardLocation.HAND:
            return self.hand

        elif location & CardLocation.MONSTER_ZONE:
            return self.monster_zones

        elif location & CardLocation.SPELL_ZONE:
            return self.spell_zones

        elif location & CardLocation.GRAVE:
            return self.graveyard

        elif location & CardLocation.BANISHED:
            return self.banished

        elif location & CardLocation.EXTRADECK:
            return self.extradeck

        else:
            return None
    

    def set_deck(self, num_of_main: int, num_of_extra: int) -> None:
        self.deck = [Card() for _ in range(num_of_main)]
        self.extradeck = [Card() for _ in range(num_of_extra)]
        

    def get_mainzone_monsters(self) -> list[Card]:
        return [zone.card for zone in self.mainmonster_zones if zone.has_card]


    def get_exzone_monsters(self) -> list[Card]:
        return [zone.card for zone in self.exmonster_zones if zone.has_card]
    

    def get_monsters(self) -> list[Card]:
        return [zone.card for zone in self.monster_zones if zone.has_card]

    
    def get_graveyard_monsters(self) -> list[Card]:
        return [card for card in self.graveyard if card.type == CardType.MONSTER]


    def get_graveyard_spells(self) -> list[Card]:
        return [card for card in self.graveyard if card.type == CardType.SPELL]
    
    
    def get_graveyard_traps(self) -> list[Card]:
        return [card for card in self.graveyard if card.type == CardType.TRAP]

    
    def get_spells(self) -> list[Card]:
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


