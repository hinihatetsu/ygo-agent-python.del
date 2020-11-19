from typing import NamedTuple

from pyYGO.field import HalfField
from pyYGO.card import Card
from pyYGO.zone import Zone
from pyYGO.enums import CardLocation, Phase, Player
from pyYGO.wrapper import Location



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
        self.life: list[int] = [8000, 8000]

        self.mainphase_end: bool = False
        self.summoning: list[Card] = []
        self.last_summoned: list[Card] = []
        self.last_summon_player: Player = None

        self.current_chain: list[Card] = []
        self.last_chain_player: Player = -1
        self.chain_targets: list[Card] = []
        self.current_chain_target: list[Card] = []

        self.field.set_zone_id()


    @property
    def players(self) -> tuple[Player]:
        return (self.first, self.second)


    def set_deck(self, player: Player, num_of_main: int, num_of_extra: int) -> None:
        self.field[player].set_deck(num_of_main, num_of_extra)


    def get_card(self, controller: Player, location: Location, index: int) -> Card:
        return self.field[controller].get_card(location, index)


    def add_card(self, card: Card, controller: Player, location: Location, index: int) -> None:
        self.field[controller].add_card(card, location, index)

    
    def remove_card(self, card: Card, controller: Player, location: Location, index: int) -> None:
        self.field[controller].remove_card(card, location, index)

    
    def get_cards(self, controller: Player, location: Location) -> list[Card]:
        if location.is_zone:
            zones: list[Zone] = self.field[controller].where(location)
            cards: list[Card] = [zone.card for zone in zones]

        else:
            cards: list[Card] = self.field[controller].where(location)

        return cards 
    

    def on_start(self, first_player: Player) -> None:
        self.__init__()
        self.first = first_player
        self.second = Player.OPPONENT if first_player == Player.ME else Player.ME


    def on_new_turn(self, turn_player: Player) -> None:
        self.turn_player = turn_player
        self.turn += 1


    def on_new_phase(self, phase: Phase) -> None:
        self.phase = phase
        for player in self.players:
            self.field[player].battling_monster = None
            self.field[player].under_attack = False

        for monster in self.field[0].get_monsters():
            monster.attacked = False

        self.mainphase_end = False
    

    def on_summoning(self, player: Player, card: Card) -> None:
        self.last_summoned.clear()
        self.summoning.append(card)
        self.last_summon_player = player

    
    def on_summoned(self) -> None:
        self.last_summoned = [card for card in self.summoning]
        self.summoning.clear()

    
    def on_spsummoned(self) -> None:
        self.on_summoned()
        for card in self.last_summoned:
            card.is_special_summoned = True

    
    def on_chaining(self, last_chain_player: Player, card: Card) -> None:
        self.last_chain_player = last_chain_player
        self.last_summon_player = -1
        self.current_chain.append(card)
        self.current_chain_target.clear()


    def on_chain_end(self) -> None:
        self.mainphase_end = False
        self.last_chain_player = -1
        self.current_chain.clear()
        self.chain_targets.clear()
        self.current_chain_target.clear()


    def on_become_target(self, card: Card) -> None:
        self.chain_targets.append(card)
        self.current_chain_target.append(card)


    def on_draw(self, player: Player) -> None:
        self.field[player].deck.pop()
        self.field[player].hand.append(Card(location=CardLocation.HAND))


    def on_damage(self, player: Player, damage: int) -> None:
        self.life[player] = max(self.life[player] - damage, 0)


    def on_recover(self, player: Player, recover: int) -> None:
        self.life[player] += recover

    
    def on_lp_update(self, player: Player, lp: int) -> None:
        self.life[player] = lp

    
    def on_attack(self, attacking: Card, attacked: Card) -> None:
        self.field[attacking.controller].battling_monster = attacking
        self.field[attacking.controller ^ 1].battling_monster = attacked
        self.field[attacking.controller ^ 1].under_attack = True


    def on_battle(self) -> None:
        self.field[Player.ME].under_attack = False
        self.field[Player.OPPONENT].under_attack = False
