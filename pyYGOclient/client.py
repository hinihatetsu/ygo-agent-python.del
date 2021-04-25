import random
import threading
import asyncio
from typing import List, Tuple, Coroutine

from pyYGO import Duel, Card, Deck
from pyYGO.zone import Zone
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.cardstatus import Location, Type, Attribute, Race, Position
from pyYGO.enums import Phase, Player, Query, CardLocation, CardPosition, CardAttribute, CardRace
from .executor import GameExecutor
from .pyYGOnetwork import YGOConnection, Packet
from .pyYGOnetwork.enums import CtosMessage, StocMessage, GameMessage, ErrorType
from debug_tools import print_message

SERVER_HANDSHAKE: int = 4043399681

class GameClient(threading.Thread):
    def __init__(self, deck_name: str, host: str, port: int, version: int, name: str) -> None:
        super().__init__()
        self._connection: YGOConnection = YGOConnection(host, port)
        self._version: int = version
        self._name: str = name
        self._duel: Duel = Duel()
        self._executor: GameExecutor = None
        self._deck: Deck = Deck(deck_name)
        self._select_hint: int = 0


    @property
    def version(self) -> int:
        return self._version


    @property
    def select_hint(self) -> int:
        return self._select_hint


    @select_hint.setter
    def select_hint(self, hint: int) -> None:
        self._select_hint = hint

    
    def get_deck(self) -> Deck:
        return self._deck


    def get_duel(self) -> Duel:
        return self._duel


    def set_executor(self, executor: GameExecutor) -> None:
        self._executor = executor


    def run(self) -> None:
        if self._executor is None:
            raise Exception('GameExecutor not set. Call .set_executor() before start.')
        asyncio.run(self._main())

    
    def surrender(self) -> None:
        self._connection.send(Packet(CtosMessage.SURRENDER))


    def close(self) -> None:
        self._connection.close()

    
    def send(self, packet: Packet) -> None:
        self._connection.send(packet)

    


    async def _main(self) -> Coroutine[None, None, None]:
        await self._connection.connect()
        if self._connection.is_connected():
            self._on_connected()
        # concurrent tasks
        response_task: asyncio.Task = asyncio.create_task(self._response())
        listen_task: asyncio.Task = asyncio.create_task(self._connection.listen())

        await response_task
        await listen_task


    async def _response(self) -> Coroutine[None, None, None]:
        while self._connection.is_connected():
            packet: Packet = await self._connection.receive_pending_packet()
            self._on_received(packet)
            await self._connection.drain()

        print('Connection closed')
    

    def chat(self, content: str) -> None:
        reply: Packet = Packet(CtosMessage.CHAT)
        reply.write(content, byte_size=2*len(content))
        reply.write(0)
        self.send(reply)


    def _on_connected(self) -> None:          
        packet: Packet = Packet(CtosMessage.PLAYER_INFO)
        packet.write(self._name, byte_size=40)
        self._connection.send(packet)

        junc = bytes([0xcc, 0xcc, 0x00, 0x00, 0x00, 0x00])
        packet = Packet(CtosMessage.JOIN_GAME)
        packet.write(self._version & 0xffff, byte_size=2)
        packet.write(junc)
        packet.write('', byte_size=40) # host_room_info here
        packet.write(self._version)
        self.send(packet)


    def _on_received(self, packet: Packet) -> None:
        msg_id: int = packet.msg_id
        if  msg_id == StocMessage.GAME_MSG:
            id: int = packet.read_int(1)
            if id == GameMessage.RETRY:
                on_retry(self, packet, self._executor)
            elif id == GameMessage.HINT:
                on_hint(self, packet, self._executor)
            elif id == GameMessage.START:
                on_start(self, packet, self._executor)
            elif id == GameMessage.WIN:
                on_win(self, packet, self._executor)
            elif id == GameMessage.NEW_TURN:
                on_new_turn(self, packet, self._executor)
            elif id == GameMessage.NEW_PHASE:
                on_new_phase(self, packet, self._executor)
            elif id == GameMessage.SELECT_IDLE_CMD:
                on_select_idle_cmd(self, packet, self._executor)
            elif id == GameMessage.SELECT_BATTLE_CMD:
                on_select_battle_cmd(self, packet, self._executor)
            elif id == GameMessage.SELECT_EFFECT_YN:
                on_select_effect_yn(self, packet, self._executor)
            elif id == GameMessage.SELECT_YESNO:
                on_select_yesno(self, packet, self._executor)
            elif id == GameMessage.SELECT_OPTION: 
                on_select_option(self, packet, self._executor)
            elif id == GameMessage.SELECT_CARD:
                on_select_card(self, packet, self._executor)
            elif id == GameMessage.SELECT_CHAIN:
                on_select_chain(self, packet, self._executor)
            elif id == GameMessage.SELECT_PLACE:
                on_select_place(self, packet, self._executor)
            elif id == GameMessage.SELECT_POSITION:
                on_select_position(self, packet, self._executor)
            elif id == GameMessage.SELECT_TRIBUTE:
                on_select_tribute(self, packet, self._executor)
            elif id == GameMessage.SELECT_COUNTER:
                on_select_counter(self, packet, self._executor)
            elif id == GameMessage.SELECT_SUM:
                on_select_sum(self, packet, self._executor)
            elif id == GameMessage.SELECT_DISFIELD:
                on_select_place(self, packet, self._executor)
            elif id == GameMessage.SELECT_UNSELECT:
                on_select_unselect(self, packet, self._executor)
            elif id == GameMessage.ANNOUNCE_RACE:
                on_announce_race(self, packet, self._executor)
            elif id == GameMessage.ANNOUNCE_ATTRIB:
                on_announce_attr(self, packet, self._executor)
            elif id == GameMessage.ANNOUNCE_CARD:
                on_announce_card(self, packet, self._executor)
            elif id == GameMessage.ANNOUNCE_NUNBER:
                on_announce_number(self, packet, self._executor)
            elif id == GameMessage.UPDATE_DATA:
                on_update_data(self, packet, self._executor)
            elif id == GameMessage.UPDATE_CARD:
                on_update_card(self, packet, self._executor)
            elif id == GameMessage.SHUFFLE_DECK:
                on_shuffle_deck(self, packet, self._executor)
            elif id == GameMessage.SHUFFLE_HAND:
                on_shuffle_hand(self, packet, self._executor)
            elif id == GameMessage.SHUFFLE_EXTRA:
                on_shuffle_extra(self, packet, self._executor)
            elif id == GameMessage.SHUFFLE_SETCARD:
                on_shuffle_setcard(self, packet, self._executor)
            elif id == GameMessage.SORT_CARD:
                on_sort_card(self, packet, self._executor)
            elif id == GameMessage.SORT_CHAIN:
                on_sort_chain(self, packet, self._executor)
            elif id == GameMessage.MOVE:
                on_move(self, packet, self._executor)
            elif id == GameMessage.POSCHANGE:
                on_poschange(self, packet, self._executor)
            elif id == GameMessage.SET:
                on_set(self, packet, self._executor)
            elif id == GameMessage.SWAP:
                on_swap(self, packet, self._executor)
            elif id == GameMessage.SUMMONING:
                on_summoning(self, packet, self._executor)
            elif id == GameMessage.SUMMONED:
                on_summoned(self, packet, self._executor)
            elif id == GameMessage.SPSUMMONING:
                on_spsummoning(self, packet, self._executor)
            elif id == GameMessage.SPSUMMONED:
                on_spsummoned(self, packet, self._executor)
            elif id == GameMessage.FLIPSUMMONING:
                on_summoning(self, packet, self._executor)
            elif id == GameMessage.FLIPSUMMONED:
                on_summoned(self, packet, self._executor)
            elif id == GameMessage.CHAINING:
                on_chaining(self, packet, self._executor)
            elif id == GameMessage.CHAIN_END:
                on_chain_end(self, packet, self._executor)
            elif id == GameMessage.BECOME_TARGET:
                on_become_target(self, packet, self._executor)
            elif id == GameMessage.DRAW:
                on_draw(self, packet, self._executor)
            elif id == GameMessage.DAMAGE:
                on_damage(self, packet, self._executor)
            elif id == GameMessage.RECOVER:
                on_recover(self, packet, self._executor)
            elif id == GameMessage.EQUIP:
                on_equip(self, packet, self._executor)
            elif id == GameMessage.UNEQUIP:
                on_unequip(self, packet, self._executor)
            elif id == GameMessage.LP_UPDATE:
                on_lp_update(self, packet, self._executor)
            elif id == GameMessage.CARD_TARGET:
                on_card_target(self, packet, self._executor)
            elif id == GameMessage.CANCEL_TARGET:
                on_cancel_target(self, packet, self._executor)
            elif id == GameMessage.PAY_LPCOST:
                on_damage(self, packet, self._executor)
            elif id == GameMessage.ATTACK:
                on_attack(self, packet, self._executor)
            elif id == GameMessage.BATTLE:
                on_battle(self, packet, self._executor)
            elif id == GameMessage.ATTACK_DISABLED:
                on_attack_disabled(self, packet, self._executor)
            elif id == GameMessage.ROCK_PAPER_SCISSORS:
                on_rock_paper_scissors(self, packet, self._executor)
            elif id == GameMessage.TAG_SWAP:
                on_tag_swap(self, packet, self._executor)

        elif msg_id == StocMessage.ERROR_MSG:
            on_error_msg(self, packet, self._executor)
        elif msg_id == StocMessage.SELECT_HAND:
            on_select_hand(self, packet, self._executor)
        elif msg_id == StocMessage.SELECT_TP:
            on_select_tp(self, packet, self._executor)
        elif msg_id == StocMessage.CHANGE_SIDE:
            on_change_side(self, packet, self._executor)
        elif msg_id == StocMessage.JOIN_GAME:
            on_joined_game(self, packet, self._executor)
        elif msg_id == StocMessage.TYPE_CHANGE:
            on_type_changed(self, packet, self._executor)
        elif msg_id == StocMessage.DUEL_START:
            on_duel_start(self, packet, self._executor)
        elif msg_id == StocMessage.DUEL_END:
            on_duel_end(self, packet, self._executor)
        elif msg_id == StocMessage.REPLAY:
            on_replay(self, packet, self._executor)
        elif msg_id == StocMessage.TIMELIMIT:
            on_timelimit(self, packet, self._executor)
        elif msg_id == StocMessage.CHAT:
            on_chat(self, packet, self._executor)
        elif msg_id == StocMessage.PLAYER_ENTER:
            on_player_enter(self, packet, self._executor)
        elif msg_id == StocMessage.PLAYER_CHANGE:
            on_player_change(self, packet, self._executor)
        elif msg_id == StocMessage.WATCH_CHANGE:
            on_watch_change(self, packet, self._executor)
        elif msg_id == StocMessage.REMATCH:
            on_rematch(self, packet, self._executor)



def on_error_msg(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    error_type: int = packet.read_int(1)
    if error_type is ErrorType.JOINERROR:
        print(error_type)

    elif error_type is ErrorType.DECKERROR:
        print(error_type)

    elif error_type is ErrorType.SIDEERROR:
        print(error_type)
    
    elif error_type is ErrorType.VERSIONERROR:
        print(error_type)

    elif error_type is ErrorType.VERSIONERROR2:
        print('Version Error')
        unknown = packet.read_int(3)
        version = packet.read_int(4)
        print(f'Host Version: {version & 0xff}.{(version >> 8) & 0xff}.{(version >> 16) & 0xff}.{(version >> 24) & 0xff}')
        print(f'Your Version: {client.version & 0xff}.{(client.version >> 8) & 0xff}.{(client.version >> 16) & 0xff}.{(client.version >> 24) & 0xff}')
    
    else:
        assert 'unknown ErrorType'
    client.close()



def on_select_hand(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    hand: int = random.randint(1, 3)
    reply: Packet = Packet(CtosMessage.HAND_RESULT)
    reply.write(hand, byte_size=1)
    client.send(reply)


def on_select_tp(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    select_first: bool = executor.select_tp()
    reply: Packet = Packet(CtosMessage.TP_RESULT)
    reply.write(select_first)
    client.send(reply)


def on_change_side(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    deck: Deck = client.get_deck()
    reply: Packet = Packet(CtosMessage.UPDATE_DECK)
    reply.write(deck.count_main + deck.count_extra)
    reply.write(deck.count_side)
    for card in deck.main + deck.extra + deck.side:
        reply.write(card)
    client.send(reply)


def on_joined_game(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    lflist: int = packet.read_int(4)
    rule: int = packet.read_int(1)
    mode: int = packet.read_int(1)
    duel_rule: int = packet.read_int(1)
    nocheck_deck: bool = packet.read_bool()
    noshuffle_deck: bool = packet.read_bool()
    align: bytes = packet.read_bytes(3)
    start_lp = packet.read_int(4)
    start_hand: int = packet.read_int(1)
    draw_count: int = packet.read_int(1)
    time_limit: int = packet.read_int(2)
    align: bytes = packet.read_bytes(4)
    handshake: int = packet.read_int(4)
    version: int = packet.read_int(4)
    team1: int = packet.read_int(4)
    team2: int = packet.read_int(4)
    best_of: int = packet.read_int(4)
    duel_flag: int = packet.read_int(4)
    forbidden_types: int = packet.read_int(4)
    extra_rules: int = packet.read_int(4)

    if handshake != SERVER_HANDSHAKE:
        print('handshake error')
        client.close()
        return
    
    deck: Deck = client.get_deck()
    reply: Packet = Packet(CtosMessage.UPDATE_DECK)
    reply.write(deck.count_main + deck.count_extra)
    reply.write(deck.count_side)
    for card in deck.main + deck.extra + deck.side:
        reply.write(card)
    client.send(reply)


def on_type_changed(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    is_spectator: int = 7
    position = packet.read_int(1)
    if position < 0 or position >= is_spectator:
        print('No position to participate')
        client.close()
        return

    client.send(Packet(CtosMessage.READY))
    return


def on_duel_start(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_duel_end(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    client.close()


def on_replay(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_timelimit(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    if player == Player.ME:  
        client.send(Packet(CtosMessage.TIME_CONFIRM))


def on_chat(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_player_enter(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    name: str = packet.read_str(40)


def on_player_change(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_watch_change(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_rematch(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    win = False
    ans: bool = executor.on_rematch(win) 
    reply: Packet = Packet(CtosMessage.REMATCH_RESPONSE)
    reply.write(ans)
    client.send(reply)



def on_retry(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    # retry means we send an invalid message
    raise Exception('sent invalid message')


def on_hint(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    HINT_EVENT = 1
    HINT_MESSAGE = 2
    HINT_SELECT = 3
    MAINPHASE_END = 23
    BATTLEING = 24
    duel: Duel = client.get_duel()
    hint_type: int = packet.read_int(1)
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    data: int = packet.read_int(8)
    if hint_type == HINT_EVENT:
        if data == MAINPHASE_END:
            duel.at_mainphase_end()
            
        elif data == BATTLEING:
            duel.field[0].under_attack = False
            duel.field[1].under_attack = False

    if hint_type == HINT_SELECT:
        client.select_hint = data


def on_start(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    is_first = not packet.read_bool()
    first_player: Player = Player.ME if is_first else Player.OPPONENT
    duel.on_start(first_player)

    for player in duel.players:
        duel.on_lp_update(player, packet.read_int(4))
    
    for player in duel.players:
        num_of_main: int = packet.read_int(2)
        num_of_extra: int = packet.read_int(2)
        duel.set_deck(player, num_of_main, num_of_extra)

    executor.on_start()
    

def on_win(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    print_message(packet.msg_id, packet.data)
    duel: Duel = client.get_duel()
    win: bool = duel.players[packet.read_int(1)] == Player.ME
    print('win' if win else 'lose')
    executor.on_win(win)
    

def on_new_turn(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    turn_player: Player = duel.players[packet.read_int(1)]
    duel.on_new_turn(turn_player)
    executor.on_new_turn()


def on_new_phase(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    phase: Phase = packet.read_phase()
    duel.on_new_phase(phase)
    executor.on_new_phase()


def on_select_idle_cmd(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)] 
    main: MainPhase = MainPhase()
    for card_list in main:
        if card_list is main.activatable: 
            for _ in range(packet.read_int(4)):
                card_id: int = packet.read_id()
                controller: Player = duel.players[packet.read_int(1)]
                location: Location = packet.read_location()
                index: int = packet.read_int(4)
                description: int = packet.read_int(8)
                operation_type: int = packet.read_int(1)

                card: Card = duel.get_card(controller, location, index)
                card.id = card_id
                main.activatable.append(card)
                main.activation_descs.append(description)

        else:
            for _ in range(packet.read_int(4)):
                card_id: int = packet.read_id()
                controller: Player = duel.players[packet.read_int(1)]
                location: Location = packet.read_location()
                index: int = packet.read_int(4) if card_list is not main.repositionable else packet.read_int(1)

                card: Card = duel.get_card(controller, location, index)
                card.id = card_id
                card_list.append(card)

    main.can_battle = packet.read_bool()
    main.can_end = packet.read_bool()
    can_shuffle = packet.read_bool()
    
    selected: int = executor.select_mainphase_action(main)
    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(selected)
    client.send(reply)


def on_select_battle_cmd(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    battle: BattlePhase = BattlePhase()

    # activatable cards
    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        description: int = packet.read_int(8)
        operation_type: bytes = packet.read_bytes(1)

        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        battle.activatable.append(card)
        battle.activation_descs.append(description)

    # attackable cards
    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(1)
        direct_attackable: bool = packet.read_bool()

        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        card.can_direct_attack = direct_attackable
        card.attacked = False
        battle.attackable.append(card)

    battle.can_main2 = packet.read_bool()
    battle.can_end = packet.read_bool()

    selected: int = executor.select_battle_action(battle)
    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(selected)
    client.send(reply)


def on_select_effect_yn(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    card_id: int = packet.read_id()
    controller: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    index: int = packet.read_int(4)
    position: Position = packet.read_position()
    description: int = packet.read_int(8)

    card: Card = duel.get_card(controller, location, index)
    card.id = card_id
    ans: bool = executor.select_effect_yn(card, description)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(ans)
    client.send(reply)


def on_select_yesno(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    REPLAY_BATTLE = 30
    player_msg_sent_to: int = duel.players[packet.read_int(1)]
    desc: int = packet.read_int(8)
    if desc == REPLAY_BATTLE:
        ans: bool = executor.select_battle_replay()
    else:
        ans: bool = executor.select_yn()
    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(ans)
    client.send(reply)


def on_select_option(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    player_msg_sent_to: int = packet.read_int(1)
    num_of_options: int = packet.read_int(1)
    options: List[int] = [packet.read_int(8) for _ in range(num_of_options)]
    ans: int = executor.select_option(options)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(ans)
    client.send(reply)


def on_select_card(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    cancelable: bool = packet.read_bool()
    min_: int = packet.read_int(4) # min number of cards to select
    max_: int = packet.read_int(4) # max number of cards to select

    choices: List[Card] = []
    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        choices.append(card)

    selected: List[int] = executor.select_card(choices, min_, max_, cancelable, client.select_hint)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(0)
    reply.write(len(selected))
    for i in selected:
        reply.write(i)
    client.send(reply)


def on_select_chain(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    specount: int = packet.read_int(1)
    forced: bool = packet.read_bool()
    hint1: int = packet.read_int(4)
    hint2: int = packet.read_int(4)

    choices: List[Card] = []
    descriptions: List[int] = []

    for _ in range(packet.read_int(4)):
        card_id = packet.read_int(4)
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        description: int = packet.read_int(8)
        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        choices.append(card)
        descriptions.append(description)
        operation_type: bytes = packet.read_bytes(1)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    if len(choices) == 0:
        reply.write(-1)
    else:
        selected: int = executor.select_chain(choices, descriptions, forced)
        reply.write(selected)
    client.send(reply)


def on_select_place(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    min_: int = packet.read_int(1)
    selectable: int = 0xffffffff - packet.read_int(4)

    player: Player = None
    location: Location = None
    is_pzone: bool = bool(selectable & (Zone.ID.PZONE | (Zone.ID.PZONE << Zone.ID.OPPONENT)))
    if selectable & Zone.ID.MONSTER_ZONE:
        player = Player.ME
        location = Location(CardLocation.MONSTER_ZONE)

    elif selectable & Zone.ID.SPELL_ZONE:
        player = Player.ME
        location = Location(CardLocation.SPELL_ZONE)

    elif selectable & (Zone.ID.MONSTER_ZONE << Zone.ID.OPPONENT):
        player = Player.OPPONENT
        location = Location(CardLocation.MONSTER_ZONE)

    elif selectable & (Zone.ID.SPELL_ZONE << Zone.ID.OPPONENT):
        player = Player.OPPONENT
        location = Location(CardLocation.SPELL_ZONE)
    
    zones: List[Zone] = duel.field[player].where(location)
    choices: List[int] = [i for i, zone in enumerate(zones) if bool(selectable & zone.id)]
    selected: int = executor.select_place(player, choices)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(duel.players.index(player), byte_size=1)
    reply.write(location.value, byte_size=1)
    reply.write(selected, byte_size=1)
    client.send(reply)


def on_select_position(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: int = duel.players[packet.read_int(1)]
    card_id: int = packet.read_id()
    selectable_position: int = packet.read_int(1)

    POSITION: List[CardPosition] = [
        CardPosition.FASEUP_ATTACK, 
        CardPosition.FASEDOWN_ATTACK, 
        CardPosition.FASEUP_DEFENCE, 
        CardPosition.FASEDOWN_DEFENCE
    ]
    
    choices: List[int] = [int(pos) for pos in POSITION if selectable_position & pos]
    selected: int = executor.select_position(card_id, choices)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(selected)
    client.send(reply)


def on_select_tribute(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    cancelable: bool = packet.read_bool()
    min_: int = packet.read_int(4) # min number of cards to select
    max_: int = packet.read_int(4) # max number of cards to select

    choices: List[Card] = []
    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        packet.read_bytes(1)
        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        choices.append(card)

    selected: List[int] = executor.select_tribute(choices, min_, max_, cancelable, client.select_hint)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(0)
    reply.write(len(selected))
    for integer in selected:
        reply.write(integer)
    client.send(reply)


def on_select_counter(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    counter_type: int = packet.read_int(2)
    quantity: int = packet.read_int(4)

    cards: List[Card] = []
    counters: List[int] = []

    for _ in range(packet.read_int(1)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(1)
        num_of_counter: int = packet.read_int(2)

        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        cards.append(card)
        counters.append(num_of_counter)

    used: List[int] = executor.select_counter(counter_type, quantity, cards, counters)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    for i in used:
        reply.write(i, byte_size=2)
    client.send(reply)


def on_select_sum(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    must_just: bool = not packet.read_bool()
    sum_value: int = packet.read_int(4)
    min_: int = packet.read_int(4)
    max_: int = packet.read_int(4)

    must_selected: List[Card] = []
    choices: List[Tuple[Card, int, int]] = []

    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        values: Tuple[int, int] = (packet.read_int(2), packet.read_int(2))
        must_selected.append(card)
        sum_value -= max(values)

    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        values: Tuple[int, int] = (packet.read_int(2), packet.read_int(2))
        choices.append((card, *values))

    selected: List[int] = executor.select_sum(choices, sum_value, min_, max_, must_just, client.select_hint)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(b'\x00\x01\x00\x00')
    reply.write(len(must_selected)+len(selected), byte_size=4)
    for _ in must_selected:
        packet.write(0, byte_size=1)
    for i in selected:
        packet.write(i, byte_size=1)
    client.send(reply)


def on_select_unselect(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_snt_to: Player = duel.players[packet.read_int(1)]
    finishable: bool = packet.read_bool()
    cancelable: bool = packet.read_bool() or finishable
    min: int = packet.read_int(4)
    max: int = packet.read_int(4)

    cards: List[Card] = []

    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()

        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        card.position = position
        cards.append(card)

    # unknown  
    for _ in range(packet.read_int(4)):
        card_id: int = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()

    max = 1
    selected: List[int] = executor.select_unselect(cards, int(not finishable), max, cancelable, client.select_hint)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    if len(selected) == 0:
        reply.write(-1)
    else:
        reply.write(len(selected))
        for integer in selected:
            reply.write(integer)
    client.send(reply)


def on_announce_race(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    count: int = packet.read_int(1)
    available: int = packet.read_int(4)
    choices: List[int] = [int(race) for race in CardRace if available & race]

    selected: List[int] = executor.announce_race(choices, count)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(sum(selected))
    client.send(reply)


def on_announce_card(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    raise Exception('not complete coding')


def on_announce_attr(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    count: int = packet.read_int(1)
    available: int = packet.read_int(4)
    choices: List[int] = [int(attr) for attr in CardAttribute if available & attr]

    selected: List[int] = executor.announce_attr(choices, count)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(sum(selected))
    client.send(reply)


def on_announce_number(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    count: int = packet.read_int(1)
    choices: List[int] = [packet.read_int(4) for _ in range(count)]
    selected: int = executor.select_number(choices)

    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(selected)
    client.send(reply)


def on_update_data(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    size: int = packet.read_int(4)
    cards: List[Card] = duel.get_cards(player, location)
    for card in cards:
        if card is not None:
            _update_card(client, card, packet)
        else:
            packet.read_bytes(2) # read \x00\x00, which means no card
    

def on_update_card(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    index: int = packet.read_int(1)

    card: Card = duel.get_card(player, location, index)
    _update_card(client, card, packet)


def _update_card(client: GameClient, card: Card, packet: Packet) -> None:
    duel: Duel = client.get_duel()
    while True:
        size: int = packet.read_int(2)
        if size == 0:
            return

        query: int = packet.read_int(4)

        if query == Query.ID:
            card.id = packet.read_int(4)

        elif query == Query.POSITION:
            card.position = Position(packet.read_int(4))

        elif query == Query.ALIAS:
            card.arias = packet.read_int(4)

        elif query == Query.TYPE:
            card.type = Type(packet.read_int(4))

        elif query == Query.LEVEL:
            card.level = packet.read_int(4)

        elif query == Query.RANK:
            card.rank = packet.read_int(4)

        elif query == Query.ATTRIBUTE:
            card.attribute = Attribute(packet.read_int(4))

        elif query == Query.RACE:
            card.race = Race(packet.read_int(4))

        elif query == Query.ATTACK:
            card.attack = packet.read_int(4)

        elif query == Query.DEFENCE:
            card.defence = packet.read_int(4)

        elif query == Query.BASE_ATTACK:
            card.base_attack = packet.read_int(4)

        elif query == Query.BASE_DEFENCE:
            card.base_defence = packet.read_int(4)

        elif query == Query.REASON:
            card.reason = packet.read_int(4)

        elif query == Query.REASON_CARD:
            controller: Player = duel.players[packet.read_int(1)]
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            card.reason_card = duel.get_card(controller, location, index)

        elif query == Query.EQUIP_CARD:
            controller: Player = duel.players[packet.read_int(1)]
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            ecard: Card = duel.get_card(controller, location, index)
            card.equip_target = ecard
            ecard.equip_cards.append(card)

        elif query == Query.TARGET_CARD:
            card.target_cards.clear()
            for _ in range(packet.read_int(4)):
                controller: Player = duel.players[packet.read_int(1)]
                location: Location = packet.read_location()
                index: int = packet.read_int(4)
                position: Position = packet.read_position()
                tcard = duel.get_card(controller, location, index)
                card.target_cards.append(tcard)
                tcard.targeted_by = card

        elif query == Query.OVERLAY_CARD:
            card.overlays.clear()
            for _ in range(packet.read_int(4)):
                card.overlays.append(packet.read_id())

        elif query == Query.COUNTERS:
            card.counters.clear()
            for _ in range(packet.read_int(4)):
                counter_info: int = packet.read_int(4)
                counter_type: int = counter_info & 0xffff
                counter_count: int = counter_info >> 16
                card.counters[counter_type] = counter_count
        
        elif query == Query.CONTROLLER:
            card.controller = duel.players[packet.read_int(1)]

        elif query == Query.STATUS:
            card.status = packet.read_int(4)

        elif query == Query.IS_PUBLIC:
            is_public: bool = packet.read_bool()

        elif query == Query.LSCALE:
            card.lscale = packet.read_int(4)

        elif query == Query.RSCALE:
            card.rscale = packet.read_int(4)

        elif query == Query.LINK:
            card.link = packet.read_int(4)
            card.linkmarker = packet.read_int(4)
        
        elif query == Query.IS_HIDDEN:
            pass

        elif query == Query.COVER:
            pass

        elif query == Query.END:
            return

        else:
            packet.read_bytes(size - 4) # 4 is bytesize of 'query'


def on_shuffle_deck(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    for card in duel.field[player].deck:
        card.id = 0


def on_shuffle_hand(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    num_of_hand: int = packet.read_int(4)
    for card in duel.field[player].hand:
        card.id = packet.read_int(4)


def on_shuffle_extra(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    num_of_extra: int = packet.read_int(4)
    for card in duel.field[player].extradeck:
        if not card.is_faceup:
            card.id = packet.read_int(4)


def on_shuffle_setcard(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    location: Location = packet.read_location()
    count: int = packet.read_int(1)

    old: List[Card] = []
    for _ in range(count):
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        card: Card = duel.get_card(controller, location, index)
        card.id = 0
        old.append(card)

    for i in range(count):
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        duel.add_card(old[i], controller, location, index)


def on_sort_card(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player_msg_sent_to: Player = duel.players[packet.read_int(1)]
    cards: List[Card] = []
    for _ in range(packet.read_int(4)):
        card_id = packet.read_id()
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        card: Card = duel.get_card(controller, location, index)
        card.id = card_id
        cards.append(card)
    
    selected: List[int] = executor.sort_card(cards)
    
    reply: Packet = Packet(CtosMessage.RESPONSE)
    for integer in selected:
        reply.write(integer, byte_size=1)
    client.send(reply)


def on_sort_chain(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    reply: Packet = Packet(CtosMessage.RESPONSE)
    reply.write(-1)
    client.send(reply)


def on_move(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    card_id: int = packet.read_id()
    # p means previous, c means current
    p_controller: Player = duel.players[packet.read_int(1)]
    p_location: Location = packet.read_location()
    p_index: int = packet.read_int(4)
    p_position: Position = packet.read_position()
    c_controller: Player = duel.players[packet.read_int(1)]
    c_location: Location = packet.read_location()
    c_index: int = packet.read_int(4)
    c_position: Position = packet.read_position()
    reason: int = packet.read_int(4)

    card: Card = duel.get_card(p_controller, p_location, p_index)
    card.id = card_id
    duel.remove_card(card, p_controller, p_location, p_index)
    duel.add_card(card, c_controller, c_location, c_index)


def on_poschange(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    card_id: int = packet.read_id()
    # p means previous, c means current
    p_controller: Player = duel.players[packet.read_int(1)]
    p_location: Location = packet.read_location()
    p_index: int = packet.read_int(1)
    p_position: Position = Position(packet.read_int(1))
    c_position: Position = Position(packet.read_int(1))

    card: Card = duel.get_card(p_controller, p_location, p_index)
    card.position = c_position


def on_set(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_swap(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    # p means previous, c means current
    card_id_1: int = packet.read_id()
    controller_1: Player = duel.players[packet.read_int(1)]
    location_1: Location = packet.read_location()
    index_1: int = packet.read_int(4)
    position_1: Position = packet.read_position()
    card_id_2: int = packet.read_id()
    controller_2: Player = duel.players[packet.read_int(1)]
    location_2: Location = packet.read_location()
    index_2: int = packet.read_int(4)
    position_2: Position = packet.read_position()

    card_1: Card = duel.get_card(controller_1, location_1, index_1)
    card_1.id = card_id_1
    card_2: Card = duel.get_card(controller_2, location_2, index_2)
    card_2.id = card_id_2

    duel.remove_card(card_1, controller_1, location_1, index_1)
    duel.remove_card(card_2, controller_2, location_2, index_2)
    duel.add_card(card_1, controller_2, location_2, index_2)
    duel.add_card(card_2, controller_1, location_1, index_1)


def on_summoning(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    card_id: int = packet.read_id()
    controller: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    index: int = packet.read_int(4)
    position: Position = packet.read_position()
    card: Card = duel.get_card(controller, location, index)
    card.id = card_id
    duel.on_summoning(controller, card)


def on_summoned(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    duel.on_summoned()


def on_spsummoning(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    card_id: int = packet.read_id()
    controller: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    index: int = packet.read_int(4)
    position: Position = packet.read_position()
    card: Card = duel.get_card(controller, location, index)
    card.id = card_id
    duel.on_summoning(controller, card)


def on_spsummoned(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    duel.on_spsummoned()


def on_chaining(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    card_id: int = packet.read_id()
    controller: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    index: int = packet.read_int(4)
    position: Position = packet.read_position()
    card: Card = duel.get_card(controller, location, index)
    card.id = card_id
    last_chain_player: Player = duel.players[packet.read_int(1)]
    duel.on_chaining(last_chain_player, card)


def on_chain_end(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    duel.on_chain_end()


def on_become_target(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    for _ in range(packet.read_int(4)):
        controller: Player = duel.players[packet.read_int(1)]
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        card: Card = duel.get_card(controller, location, index)
        duel.on_become_target(card)


def on_draw(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    for _ in range(packet.read_int(4)):
        duel.on_draw(player)


def on_damage(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    damage: int = packet.read_int(4)
    duel.on_damage(player, damage)


def on_recover(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    recover: int = packet.read_int(4)
    duel.on_recover(player, recover)


def on_equip(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    controller_1: Player = duel.players[packet.read_int(1)]
    location_1: Location = packet.read_location()
    index_1: int = packet.read_int(4)
    position_1: Position = packet.read_position()
    controller_2: Player = duel.players[packet.read_int(1)]
    location_2: Location = packet.read_location()
    index_2: int = packet.read_int(4)
    position_2: Position = packet.read_position()

    equip: Card = duel.get_card(controller_1, location_1, index_1)
    equipped: Card = duel.get_card(controller_2, location_2, index_2)

    if equip.equip_target is not None:
        equip.equip_target.equip_cards.remove(equip)
    equip.equip_target = equipped
    equipped.equip_cards.append(equip)


def on_unequip(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    controller: Player = duel.players[packet.read_int(1)]
    location: Location = packet.read_location()
    index: int = packet.read_int(4)
    position: Position = packet.read_position()
    equip: Card = duel.get_card(controller, location, index)
    equip.equip_target.equip_cards.remove(equip)
    equip.equip_target = None


def on_lp_update(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    player: Player = duel.players[packet.read_int(1)]
    lp: int = packet.read_int(4)
    duel.on_lp_update(player, lp)


def on_card_target(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    controller_1: Player = duel.players[packet.read_int(1)]
    location_1: Location = packet.read_location()
    index_1: int = packet.read_int(4)
    position_1: Position = packet.read_position()
    controller_2: Player = duel.players[packet.read_int(1)]
    location_2: Location = packet.read_location()
    index_2: int = packet.read_int(4)
    position_2: Position = packet.read_position()
    targeting: Card = duel.get_card(controller_1, location_1, index_1)
    targeted: Card = duel.get_card(controller_2, location_2, index_2)
    targeting.target_cards.append(targeted)
    targeted.targeted_by.append(targeting)


def on_cancel_target(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    controller_1: Player = duel.players[packet.read_int(1)]
    location_1: Location = packet.read_location()
    index_1: int = packet.read_int(4)
    position_1: Position = packet.read_position()
    controller_2: Player = duel.players[packet.read_int(1)]
    location_2: Location = packet.read_location()
    index_2: int = packet.read_int(4)
    position_2: Position = packet.read_position()
    targeting: Card = duel.get_card(controller_1, location_1, index_1)
    targeted: Card = duel.get_card(controller_2, location_2, index_2)
    targeting.target_cards.remove(targeted)
    targeted.targeted_by.remove(targeting)


def on_attack(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    controller_1: Player = duel.players[packet.read_int(1)]
    location_1: Location = packet.read_location()
    index_1: int = packet.read_int(4)
    position_1: Position = packet.read_position()
    controller_2: Player = duel.players[packet.read_int(1)]
    location_2: Location = packet.read_location()
    index_2: int = packet.read_int(4)
    position_2: Position = packet.read_position()
    attacking: Card = duel.get_card(controller_1, location_1, index_1)
    attacked: Card = duel.get_card(controller_2, location_2, index_2)
    duel.on_attack(attacking, attacked)
    

def on_battle(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    duel.on_battle()


def on_attack_disabled(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    duel: Duel = client.get_duel()
    duel.on_battle()


def on_rock_paper_scissors(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass


def on_tag_swap(client: GameClient, packet: Packet, executor: GameExecutor) -> None:
    pass

