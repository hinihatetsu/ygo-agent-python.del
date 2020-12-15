from typing import NamedTuple

from .field import HalfField
from .card import Card
from .zone import Zone
from .enums import CardLocation, Phase, Player
from .wrapper import Location



class DuelField(NamedTuple):
    myside: HalfField
    opside: HalfField

    def set_zone_id(self) -> None:
        for i, mzone in enumerate(self.myside.monster_zones):
            mzone.id = Zone.ID.MZONE_0 << i
        for i, szone in enumerate(self.myside.spell_zones):
            szone.id = Zone.ID.SZONE_0 << i
        for i, mzone in enumerate(self.opside.monster_zones):
            mzone.id = Zone.ID.MZONE_0 << i << Zone.ID.OPPONENT
        for i, szone in enumerate(self.opside.spell_zones):
            szone.id = Zone.ID.SZONE_0 << i << Zone.ID.OPPONENT


class Duel:
    def __init__(self) -> None:
        self._field: DuelField = DuelField(HalfField(), HalfField())
        self._first: Player = Player.NONE
        self._second: Player = Player.NONE
        self._turn_player: Player = Player.NONE
        self._turn: int = 0
        self._phase: Phase = Phase.DRAW
        self._life: list[int] = [8000, 8000]

        self._mainphase_end: bool = False
        self._summoning: list[Card] = []
        self._last_summoned: list[Card] = []
        self._last_summon_player: Player = Player.NONE

        self._current_chain: list[Card] = []
        self._last_chain_player: Player = Player.NONE
        self._chain_targets: list[Card] = []
        self._current_chain_target: list[Card] = []

        self._field.set_zone_id()


    @property
    def players(self) -> tuple[Player, Player]:
        return self._first, self._second

    @property
    def turn_player(self) -> Player:
        return self._turn_player

    @property
    def turn(self) -> int:
        return self._turn

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def life(self) -> list[int]:
        return self._life
    
    @property 
    def field(self) -> DuelField:
        return self._field

    @property
    def current_chain(self) -> list[Card]:
        return self._current_chain

    @property
    def last_chain_player(self) -> Player:
        return self._last_chain_player

    @property
    def chain_targets(self) -> list[Card]:
        return self._chain_targets


    def set_deck(self, player: Player, num_of_main: int, num_of_extra: int) -> None:
        self._field[player].set_deck(num_of_main, num_of_extra)


    def get_card(self, controller: Player, location: Location, index: int) -> Card:
        return self._field[controller].get_card(location, index)


    def add_card(self, card: Card, controller: Player, location: Location, index: int) -> None:
        card.controller = controller
        card.location = location
        self._field[controller].add_card(card, location, index)

    
    def remove_card(self, card: Card, controller: Player, location: Location, index: int) -> None:
        self._field[controller].remove_card(card, location, index)

    
    def get_cards(self, controller: Player, location: Location) -> list[Card]:
        if location.is_zone:
            zones: list[Zone] = self._field[controller].where(location)
            cards: list[Card] = [zone.card for zone in zones]

        else:
            cards = self._field[controller].where(location)

        return cards 
    

    def at_mainphase_end(self) -> None:
        self._mainphase_end = True


    def on_start(self, first_player: Player) -> None:
        self.__init__()
        self._first = first_player
        self._second = Player.OPPONENT if first_player == Player.ME else Player.ME


    def on_new_turn(self, turn_player: Player) -> None:
        self._turn_player = turn_player
        self._turn += 1


    def on_new_phase(self, phase: Phase) -> None:
        self._phase = phase
        for player in self.players:
            self._field[player].battling_monster = None
            self._field[player].under_attack = False

        for monster in self._field[0].get_monsters():
            monster.attacked = False

        self._mainphase_end = False
    

    def on_summoning(self, player: Player, card: Card) -> None:
        self._last_summoned.clear()
        self._summoning.append(card)
        self._last_summon_player = player

    
    def on_summoned(self) -> None:
        self._last_summoned = [card for card in self._summoning]
        self._summoning.clear()

    
    def on_spsummoned(self) -> None:
        self.on_summoned()
        for card in self._last_summoned:
            card.is_special_summoned = True

    
    def on_chaining(self, last_chain_player: Player, card: Card) -> None:
        self._last_chain_player = last_chain_player
        self._last_summon_player = Player.NONE
        self._current_chain.append(card)
        self._current_chain_target.clear()


    def on_chain_end(self) -> None:
        self._mainphase_end = False
        self._last_chain_player = -1
        self._current_chain.clear()
        self._chain_targets.clear()
        self._current_chain_target.clear()


    def on_become_target(self, card: Card) -> None:
        self._chain_targets.append(card)
        self._current_chain_target.append(card)


    def on_draw(self, player: Player) -> None:
        self._field[player].deck.pop()
        self._field[player].hand.append(Card(location=Location(CardLocation.HAND)))


    def on_damage(self, player: Player, damage: int) -> None:
        self._life[player] = max(self._life[player] - damage, 0)


    def on_recover(self, player: Player, recover: int) -> None:
        self._life[player] += recover

    
    def on_lp_update(self, player: Player, lp: int) -> None:
        self._life[player] = lp

    
    def on_attack(self, attacking: Card, attacked: Card) -> None:
        self._field[attacking.controller].battling_monster = attacking
        self._field[attacking.controller ^ 1].battling_monster = attacked
        self._field[attacking.controller ^ 1].under_attack = True


    def on_battle(self) -> None:
        self._field[Player.ME].under_attack = False
        self._field[Player.OPPONENT].under_attack = False
