import asyncio
import random
from typing import Callable, Coroutine

from pyYGO import Duel, Card, Zone, Location, Deck
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import Phase, Player, CardLocation, CardPosition, CardType, Attribute, Query, Race
from .player import GamePlayer
from .pyYGOnetwork import YGOConnection, Packet, CtosMessage, StocMessage, GameMessage
from debug_tools import print_message


class GameClient:
    SERVER_HANDSHAKE: int = 4043399681
    def __init__(self, host: str, port: int, version: int, name: str) -> None:
        self._connection: YGOConnection = YGOConnection(host, port)
        self._version: int = version
        self._name: str = name
        self._duel: Duel = Duel()
        self._gameplayer: GamePlayer = None
        self._deck: Deck = None

        self._select_hint: int = 0
        self._best_of: int = 0
        self._win: int = 0

        self._StocMessage_to_func: dict[StocMessage, Callable] = {
            StocMessage.ERROR_MSG:     self._on_error_msg,
            StocMessage.SELECT_HAND:   self._on_select_hand,
            StocMessage.SELECT_TP:     self._on_select_tp,
            StocMessage.CHANGE_SIDE:   self._on_change_side,
            StocMessage.JOIN_GAME:     self._on_joined_game,
            StocMessage.TYPE_CHANGE:   self._on_type_changed,
            StocMessage.DUEL_START:    self._on_duel_start,
            StocMessage.DUEL_END:      self._on_duel_end,
            StocMessage.REPLAY:        self._on_replay,
            StocMessage.TIMELIMIT:     self._on_timelimit,
            StocMessage.CHAT:          self._on_chat,
            StocMessage.PLAYER_ENTER:  self._on_player_enter,
            StocMessage.PLAYER_CHANGE: self._on_player_change,
            StocMessage.WATCH_CHANGE:  self._on_watch_change,
            StocMessage.REMATCH:       self._on_rematch
        }
        self._GameMessage_to_func: dict[GameMessage, Callable] = {
            GameMessage.RETRY:              self._on_retry,
            GameMessage.HINT:               self._on_hint,
            GameMessage.START:              self._on_start,
            GameMessage.WIN:                self._on_win,
            GameMessage.NEW_TURN:           self._on_new_turn,
            GameMessage.NEW_PHASE:          self._on_new_phase,
            GameMessage.SELECT_IDLE_CMD:    self._on_select_idle_cmd,
            GameMessage.SELECT_BATTLE_CMD:  self._on_select_battle_cmd,
            GameMessage.SELECT_EFFECT_YN:   self._on_select_effect_yn,
            GameMessage.SELECT_YESNO:       self._on_select_yesno,
            GameMessage.SELECT_OPTION:      self._on_select_option,
            GameMessage.SELECT_CARD:        self._on_select_card,
            GameMessage.SELECT_CHAIN:       self._on_select_chain,
            GameMessage.SELECT_PLACE:       self._on_select_place,
            GameMessage.SELECT_POSITION:    self._on_select_position,
            GameMessage.SELECT_TRIBUTE:     self._on_select_tribute,
            GameMessage.SELECT_COUNTER:     self._on_select_counter,
            GameMessage.SELECT_SUM:         self._on_select_sum,
            GameMessage.SELECT_DISFIELD:    self._on_select_place,
            GameMessage.SELECT_UNSELECT:    self._on_select_unselect,
            GameMessage.ANNOUNCE_RACE:      self._on_announce_race,
            GameMessage.ANNOUNCE_ATTRIB:    self._on_announce_attr,
            GameMessage.ANNOUNCE_CARD:      self._on_announce_card,
            GameMessage.ANNOUNCE_NUNBER:    self._on_announce_number,
            GameMessage.UPDATE_DATA:        self._on_update_data,
            GameMessage.UPDATE_CARD:        self._on_update_card,
            GameMessage.SHUFFLE_DECK:       self._on_shuffle_deck,
            GameMessage.SHUFFLE_HAND:       self._on_shuffle_hand,
            GameMessage.SHUFFLE_EXTRA:      self._on_shuffle_extra,
            GameMessage.SHUFFLE_SETCARD:    self._on_shuffle_setcard,
            GameMessage.SORT_CARD:          self._on_sort_card,
            GameMessage.SORT_CHAIN:         self._on_sort_chain,
            GameMessage.MOVE:               self._on_move,
            GameMessage.POSCHANGE:          self._on_poschange,
            GameMessage.SET:                self._on_set,
            GameMessage.SWAP:               self._on_swap,
            GameMessage.SUMMONING:          self._on_summoning,
            GameMessage.SUMMONED:           self._on_summoned,
            GameMessage.SPSUMMONING:        self._on_spsummoning,
            GameMessage.SPSUMMONED:         self._on_spsummoned,
            GameMessage.FLIPSUMMONING:      self._on_summoning,
            GameMessage.FLIPSUMMONED:       self._on_summoned,
            GameMessage.CHAINING:           self._on_chaining,
            GameMessage.CHAIN_END:          self._on_chain_end,
            GameMessage.BECOME_TARGET:      self._on_become_target,
            GameMessage.DRAW:               self._on_draw,
            GameMessage.DAMAGE:             self._on_damage,
            GameMessage.RECOVER:            self._on_recover,
            GameMessage.EQUIP:              self._on_equip,
            GameMessage.UNEQUIP:            self._on_unequip,
            GameMessage.LP_UPDATE:          self._on_lp_update,
            GameMessage.CARD_TARGET:        self._on_card_target,
            GameMessage.CANCEL_TARGET:      self._on_cancel_target,
            GameMessage.PAY_LPCOST:         self._on_damage,
            GameMessage.ATTACK:             self._on_attack,
            GameMessage.BATTLE:             self._on_battle,
            GameMessage.ATTACK_DISABLED:    self._on_attack_disabled,
            GameMessage.ROCK_PAPER_SCISSORS:self._on_rock_paper_scissors,
            GameMessage.TAG_SWAP:           self._on_tag_swap,
        }

        
    def get_duel(self) -> Duel:
        return self._duel


    def set_gameplayer(self, gameplayer: GamePlayer) -> None:
        self._gameplayer = gameplayer


    def set_deck(self, deck: Deck) -> None:
        self._deck = deck


    def start(self) -> None:
        if self._gameplayer is None:
            raise Exception('GamePlayer not set. Call GameClient.set_gameplayer() before start.')
        if self._deck is None:
            raise Exception('Deck not set. Call GameClient.set_deck() before start.')
        asyncio.run(self._main())


    async def _main(self) -> Coroutine[None, None, None]:
        await self._connection.connect()
        if self._connection.is_connected:
            self._on_connected()
        # concurrent tasks
        response_task: asyncio.Task = asyncio.create_task(self._main_loop())
        listen_task: asyncio.Task = asyncio.create_task(self._connection.listen())

        await response_task
        await listen_task
        

    async def _main_loop(self) -> Coroutine[None, None, None]:
        while self._connection.is_connected:
            packet: Packet = await self._connection.receive_pending_packet()
            self._on_recieved(packet)
            await self._connection.drain()
        self._gameplayer.on_close()

    
    def _chat(self, content: str) -> None:
        reply: Packet = Packet(CtosMessage.CHAT)
        reply.write(content, byte_size=2*len(content))
        reply.write(0)
        self._connection.send(reply)


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
        self._connection.send(packet)


    def _on_recieved(self, packet: Packet) -> None:
        if packet.msg_id == StocMessage.GAME_MSG:
            id: int = packet.read_int(1)
            if id in self._GameMessage_to_func:
                self._GameMessage_to_func[GameMessage(id)](packet)
            else:
                pass
                #print(f'unsupported GameMessage: {id}')
            return

        if packet.msg_id in self._StocMessage_to_func:
            self._StocMessage_to_func[StocMessage(packet.msg_id)](packet)
        else:
            pass
            #print(f'unsupported StocMessage: {packet.msg_id}')


    def _on_error_msg(self, packet: Packet) -> None:
        print('error on server')
        self._connection.close()


    def _on_select_hand(self, packet: Packet) -> None:
        hand: int = random.randint(1, 3)
        reply: Packet = Packet(CtosMessage.HAND_RESULT)
        reply.write(hand, byte_size=1)
        self._connection.send(reply)


    def _on_select_tp(self, packet: Packet) -> None:
        select_first: bool = self._gameplayer.select_tp()
        reply: Packet = Packet(CtosMessage.TP_RESULT)
        reply.write(select_first)
        self._connection.send(reply)


    def _on_change_side(self, packet: Packet) -> None:
        reply: Packet = Packet(CtosMessage.UPDATE_DECK)
        reply.write(self._deck.count_main + self._deck.count_extra)
        reply.write(self._deck.count_side)
        for card in self._deck.main + self._deck.extra + self._deck.side:
            reply.write(card)
        self._connection.send(reply)


    def _on_joined_game(self, packet: Packet) -> None:
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

        if handshake != self.SERVER_HANDSHAKE:
            self._connection.close()
            return

        self._best_of = best_of
        reply: Packet = Packet(CtosMessage.UPDATE_DECK)
        reply.write(self._deck.count_main + self._deck.count_extra)
        reply.write(self._deck.count_side)
        for card in self._deck.main + self._deck.extra + self._deck.side:
            reply.write(card)
        self._connection.send(reply)


    def _on_type_changed(self, packet: Packet) -> None:
        is_spectator: int = 7
        position = packet.read_int(1)
        if position < 0 or position >= is_spectator:
            self._connection.close()
            return

        self._connection.send(Packet(CtosMessage.READY))
        return


    def _on_duel_start(self, packet: Packet) -> None:
        pass


    def _on_duel_end(self, packet: Packet) -> None:
        self._connection.close()


    def _on_replay(self, packet: Packet) -> None:
        pass


    def _on_timelimit(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        if player == Player.ME:  
            self._connection.send(Packet(CtosMessage.TIME_CONFIRM))


    def _on_chat(self, packet: Packet) -> None:
        pass


    def _on_player_enter(self, packet: Packet) -> None:
        name: str = packet.read_str(40)


    def _on_player_change(self, packet: Packet) -> None:
        pass


    def _on_watch_change(self, packet: Packet) -> None:
        pass


    def _on_rematch(self, packet: Packet) -> None:
        win: bool = (2 * self._win > self._best_of)
        ans: bool = self._gameplayer.on_rematch(win)
        self._win = 0 
        reply: Packet = Packet(CtosMessage.REMATCH_RESPONSE)
        reply.write(ans)
        self._connection.send(reply)

    
    
    def _on_retry(self, packet: Packet) -> None:
        # retry means we send an invalid message
        print_message(self._connection.last_recieved.msg_id, self._connection.last_recieved.content)
        print_message(self._connection.last_send.msg_id, self._connection.last_send.content, send=True)
        raise Exception('sent invalid message')


    def _on_hint(self, packet: Packet) -> None:
        HINT_EVENT = 1
        HINT_MESSAGE = 2
        HINT_SELECT = 3
        MAINPHASE_END = 23
        BATTLEING = 24
        hint_type: int = packet.read_int(1)
        player_msg_sent_to: Player = packet.read_player()
        data: int = packet.read_int(8)
        if hint_type == HINT_EVENT:
            if data == MAINPHASE_END:
                self._duel.at_mainphase_end()
                
            elif data == BATTLEING:
                self._duel.field[0].under_attack = False
                self._duel.field[1].under_attack = False

        if hint_type == HINT_SELECT:
            self._select_hint = data

    
    def _on_start(self, packet: Packet) -> None:
        Packet.first_is_me = not packet.read_bool()
        first_player: Player = Player.ME if Packet.first_is_me else Player.OPPONENT
        self._duel.on_start(first_player)

        for player in self._duel.players:
            self._duel.on_lp_update(player, packet.read_int(4))
        
        for player in self._duel.players:
            num_of_main: int = packet.read_int(2)
            num_of_extra: int = packet.read_int(2)
            self._duel.set_deck(player, num_of_main, num_of_extra)

        self._gameplayer.on_start()
        

    def _on_win(self, packet: Packet) -> None:
        win: bool = packet.read_player() == Player.ME
        if win:
            self._win += 1
        self._gameplayer.on_win(win)
        

    def _on_new_turn(self, packet: Packet) -> None:
        turn_player: Player = packet.read_player()
        self._duel.on_new_turn(turn_player)
        self._gameplayer.on_new_turn()


    def _on_new_phase(self, packet: Packet) -> None:
        phase: Phase = packet.read_phase()
        self._duel.on_new_phase(phase)
        self._gameplayer.on_new_phase()


    def _on_select_idle_cmd(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player() 
        main: MainPhase = MainPhase()
        for card_list in main:
            if card_list is main.activatable: 
                for _ in range(packet.read_int(4)):
                    card_id: int = packet.read_id()
                    controller: Player = packet.read_player()
                    location: Location = packet.read_location()
                    index: int = packet.read_int(4)
                    description: int = packet.read_int(8)
                    operation_type: int = packet.read_int(1)

                    card: Card = self._duel.get_card(controller, location, index)
                    card.id = card_id
                    main.activatable.append(card)
                    main.activation_descs.append(description)

            else:
                for _ in range(packet.read_int(4)):
                    card_id: int = packet.read_id()
                    controller: Player = packet.read_player()
                    location: Location = packet.read_location()
                    index: int = packet.read_int(4) if card_list is not main.repositionable else packet.read_int(1)

                    card: Card = self._duel.get_card(controller, location, index)
                    card.id = card_id
                    card_list.append(card)

        main.can_battle = packet.read_bool()
        main.can_end = packet.read_bool()
        can_shuffle = packet.read_bool()
        
        selected: int = self._gameplayer.select_mainphase_action(main)
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self._connection.send(reply)


    def _on_select_battle_cmd(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        battle: BattlePhase = BattlePhase()

        # activatable cards
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            description: int = packet.read_int(8)
            operation_type: bytes = packet.read_bytes(1)

            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            battle.activatable.append(card)
            battle.activation_descs.append(description)

        # attackable cards
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(1)
            direct_attackable: bool = packet.read_bool()

            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            card.can_direct_attack = direct_attackable
            card.attacked = False
            battle.attackable.append(card)

        battle.can_main2 = packet.read_bool()
        battle.can_end = packet.read_bool()

        selected: int = self._gameplayer.select_battle_action(battle)
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self._connection.send(reply)


    def _on_select_effect_yn(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        description: int = packet.read_int(8)

        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        ans: bool = self._gameplayer.select_effect_yn(card, description)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self._connection.send(reply)


    def _on_select_yesno(self, packet: Packet) -> None:
        REPLAY_BATTLE = 30
        player_msg_sent_to: int = packet.read_player()
        desc: int = packet.read_int(8)
        if desc == REPLAY_BATTLE:
            ans: bool = self._gameplayer.select_battle_replay()
        else:
            ans: bool = self._gameplayer.select_yn()
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self._connection.send(reply)


    def _on_select_option(self, packet: Packet) -> None:
        player_msg_sent_to: int = packet.read_int(1)
        num_of_options: int = packet.read_int(1)
        options: list[int] = [packet.read_int(8) for _ in range(num_of_options)]
        ans: int = self._gameplayer.select_option(options)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self._connection.send(reply)


    def _on_select_card(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        cancelable: bool = packet.read_bool()
        min_: int = packet.read_int(4) # min number of cards to select
        max_: int = packet.read_int(4) # max number of cards to select

        choices: list[Card] = []
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            choices.append(card)

        selected: list[int] = self._gameplayer.select_card(choices, min_, max_, cancelable, self._select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(0)
        reply.write(len(selected))
        for i in selected:
            reply.write(i)
        self._connection.send(reply)


    def _on_select_chain(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        specount: int = packet.read_int(1)
        forced: bool = packet.read_bool()
        hint1: int = packet.read_int(4)
        hint2: int = packet.read_int(4)

        choices: list[Card] = []
        descriptions: list[int] = []

        for _ in range(packet.read_int(4)):
            card_id = packet.read_int(4)
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            description: int = packet.read_int(8)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            choices.append(card)
            descriptions.append(description)
            operation_type: bytes = packet.read_bytes(1)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        if len(choices) == 0:
            reply.write(-1)
        else:
            selected: int = self._gameplayer.select_chain(choices, descriptions, forced)
            reply.write(selected)
        self._connection.send(reply)


    def _on_select_place(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
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
        
        selected: int = self._gameplayer.select_place(player, location, selectable, is_pzone)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(player)
        reply.write(int(location), byte_size=1)
        reply.write(selected, byte_size=1)
        self._connection.send(reply)


    def _on_select_position(self, packet: Packet) -> None:
        player_msg_sent_to: int = packet.read_player()
        card_id: int = packet.read_id()
        selectable_position: CardPosition = packet.read_int(1)

        POSITION: list[CardPosition] = [
            CardPosition.FASEUP_ATTACK, 
            CardPosition.FASEDOWN_ATTACK, 
            CardPosition.FASEUP_DEFENCE, 
            CardPosition.FASEDOWN_DEFENCE
        ]
        
        choices: list[CardPosition] = [pos for pos in POSITION if selectable_position & pos]
        selected: int = self._gameplayer.select_position(card_id, choices)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self._connection.send(reply)


    def _on_select_tribute(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        cancelable: bool = packet.read_bool()
        min_: int = packet.read_int(4) # min number of cards to select
        max_: int = packet.read_int(4) # max number of cards to select

        choices: list[Card] = []
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            packet.read_bytes(1)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            choices.append(card)

        selected: list[int] = self._gameplayer.select_tribute(choices, min_, max_, cancelable, self._select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(0)
        reply.write(len(selected))
        for integer in selected:
            reply.write(integer)
        self._connection.send(reply)


    def _on_select_counter(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        counter_type: int = packet.read_int(2)
        quantity: int = packet.read_int(4)

        cards: list[Card] = []
        counters: list[int] = []

        for _ in range(packet.read_int(1)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(1)
            num_of_counter: int = packet.read_int(2)

            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            cards.append(card)
            counters.append(num_of_counter)

        used: list[int] = self._gameplayer.select_counter(counter_type, quantity, cards, counters)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        for i in used:
            reply.write(i, byte_size=2)
        self._connection.send(reply)


    def _on_select_sum(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        must_just: bool = not packet.read_bool()
        sum_value: int = packet.read_int(4)
        min_: int = packet.read_int(4)
        max_: int = packet.read_int(4)

        must_selected: list[Card] = []
        choices: list[tuple[Card, int, int]] = []

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            values: tuple[int, int] = (packet.read_int(2), packet.read_int(2))
            must_selected.append(card)
            sum_value -= max(values)

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            values: tuple[int, int] = (packet.read_int(2), packet.read_int(2))
            choices.append((card, *values))

        selected: list[int] = self._gameplayer.select_sum(choices, sum_value, min_, max_, must_just, self._select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(b'\x00\x01\x00\x00')
        reply.write(len(must_selected)+len(selected), byte_size=4)
        for _ in must_selected:
            packet.write(0, byte_size=1)
        for i in selected:
            packet.write(i, byte_size=1)
        self._connection.send(reply)


    def _on_select_unselect(self, packet: Packet) -> None:
        player_msg_snt_to: Player = packet.read_player()
        finishable: bool = packet.read_bool()
        cancelable: bool = packet.read_bool() or finishable
        min: int = packet.read_int(4)
        max: int = packet.read_int(4)

        cards: list[Card] = []

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()

            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            card.position = position
            cards.append(card)

        # unknown  
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()

        max = 1
        selected: list[int] = self._gameplayer.select_unselect(cards, int(not finishable), max, cancelable, self._select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        if len(selected) == 0:
            reply.write(-1)
        else:
            reply.write(len(selected))
            for integer in selected:
                reply.write(integer)
        self._connection.send(reply)


    def _on_announce_race(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        available: int = packet.read_int(4)
        choices: list[Race] = [race for race in Race if available & race]

        selected: list[int] = self._gameplayer.announce_race(choices, count)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(sum(selected))
        self._connection.send(reply)


    def _on_announce_card(self, packet: Packet) -> None:
        raise Exception('not complete coding')


    def _on_announce_attr(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        available: int = packet.read_int(4)
        choices: list[Attribute] = [attr for attr in Attribute if available & attr]

        selected: list[int] = self._gameplayer.announce_attr(choices, count)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(sum(selected))
        self._connection.send(reply)


    def _on_announce_number(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        choices: list[int] = [packet.read_int(4) for _ in range(count)]
        selected: int = self._gameplayer.select_number(choices)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self._connection.send(reply)


    def _on_update_data(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        location: Location = packet.read_location()
        cards: list[Card] = self._duel.get_cards(player, location)
        size: int = packet.read_int(4)
        for card in cards:
            if card is not None:
                self._update_card(card, packet)
            else:
                packet.read_bytes(2) # read \x00\x00, which means no card
        

    def _on_update_card(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(1)

        card: Card = self._duel.get_card(player, location, index)
        self._update_card(card, packet)

    
    def _update_card(self, card: Card, packet: Packet) -> None:
        while True:
            size: int = packet.read_int(2)
            if size == 0:
                return

            query: int = packet.read_int(4)
            if query == Query.ID:
                card.id = packet.read_int(4)
    
            elif query == Query.POSITION:
                pos = packet.read_int(4)
                card.position = card.POSITION[pos] if pos in card.POSITION else pos

            elif query == Query.ALIAS:
                card.arias = packet.read_int(4)

            elif query == Query.TYPE:
                type_ = packet.read_int(4)
                card.type.clear()
                for t in CardType:
                    if type_ & t:
                        card.type.append(t)

            elif query == Query.LEVEL:
                card.level = packet.read_int(4)

            elif query == Query.RANK:
                card.rank = packet.read_int(4)

            elif query == Query.ATTRIBUTE:
                attr = packet.read_int(4)
                card.attribute = card.ATTRIBUTE[attr] if attr in card.ATTRIBUTE else attr

            elif query == Query.RACE:
                race = packet.read_int(4)
                card.race = card.RASE[race] if race in card.RASE else race 

            elif query == Query.ATTACK:
                card.attack = packet.read_int(4)

            elif query == Query.DEFENCE:
                card.defence = packet.read_int(4)

            elif query == Query.BASE_ATTACK:
                card.base_attack = packet.read_int(4)

            elif query == Query.BASE_DEFENCE:
                card.base_defence = packet.read_int(4)

            elif query == Query.OVERLAY_CARD:
                for _ in range(packet.read_int(4)):
                    card.overlays.append(packet.read_id())

            elif query == Query.CONTROLLER:
                card.controller = packet.read_player()

            elif query == Query.STATUS:
                DISABLED = 0x0001
                PROC_COMPLETE = 0x0008
                status: int = packet.read_int(4)
                card.disabled = bool(status & DISABLED)
                card.proc_complete = bool(status & PROC_COMPLETE)

            elif query == Query.LSCALE:
                card.lscale = packet.read_int(4)

            elif query == Query.RSCALE:
                card.rscale = packet.read_int(4)

            elif query == Query.LINK:
                card.links = packet.read_int(4)
                card.linkmarker = packet.read_int(4)

            elif query == Query.END:
                return

            else:
                packet.read_bytes(size - 4) # 4 is bytesize of 'query'


    def _on_shuffle_deck(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        for card in self._duel.field[player].deck:
            card.id = 0


    def _on_shuffle_hand(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_of_hand: int = packet.read_int(4)
        for card in self._duel.field[player].hand:
            card.id = packet.read_int(4)

    
    def _on_shuffle_extra(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_of_extra: int = packet.read_int(4)
        for card in self._duel.field[player].extradeck:
            if not card.is_faceup:
                card.id = packet.read_int(4)


    def _on_shuffle_setcard(self, packet: Packet) -> None:
        location: Location = packet.read_location()
        count: int = packet.read_int(1)

        old: list[Card] = []
        for _ in range(count):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            card: Card = self._duel.get_card(controller, location, index)
            card.id = 0
            old.append(card)

        for i in range(count):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            self._duel.add_card(old[i], controller, location, index)

    
    def _on_sort_card(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        cards: list[Card] = []
        for _ in range(packet.read_int(4)):
            card_id = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            cards.append(card)
        
        selected: list[int] = self._gameplayer.sort_card(cards)
        
        reply: Packet = Packet(CtosMessage.RESPONSE)
        for integer in selected:
            reply.write(integer, byte_size=1)
        self._connection.send(reply)


    def _on_sort_chain(self, packet: Packet) -> None:
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(-1)
        self._connection.send(reply)


    def _on_move(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        # p means previous, c means current
        p_controller: Player = packet.read_player()
        p_location: Location = packet.read_location()
        p_index: int = packet.read_int(4)
        p_position: CardPosition = packet.read_position()
        c_controller: Player = packet.read_player()
        c_location: Location = packet.read_location()
        c_index: int = packet.read_int(4)
        c_position: CardPosition = packet.read_position()
        reason: int = packet.read_int(4)

        card: Card = self._duel.get_card(p_controller, p_location, p_index)
        card.id = card_id
        self._duel.remove_card(card, p_controller, p_location, p_index)
        self._duel.add_card(card, c_controller, c_location, c_index)


    def _on_poschange(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        # p means previous, c means current
        p_controller: Player = packet.read_player()
        p_location: Location = packet.read_location()
        p_index: int = packet.read_int(1)
        p_position: CardPosition = CardPosition(packet.read_int(1))
        c_position: CardPosition = CardPosition(packet.read_int(1))

        card: Card = self._duel.get_card(p_controller, p_location, p_index)
        card.position = c_position


    def _on_set(self, packet: Packet) -> None:
        pass


    def _on_swap(self, packet: Packet) -> None:
        # p means previous, c means current
        card_id_1: int = packet.read_id()
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: CardPosition = packet.read_position()
        card_id_2: int = packet.read_id()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: CardPosition = packet.read_position()

        card_1: Card = self._duel.get_card(controller_1, location_1, index_1)
        card_1.id = card_id_1
        card_2: Card = self._duel.get_card(controller_2, location_2, index_2)
        card_2.id = card_id_2

        self._duel.remove_card(card_1, controller_1, location_1, index_1)
        self._duel.remove_card(card_2, controller_2, location_2, index_2)
        self._duel.add_card(card_1, controller_2, location_2, index_2)
        self._duel.add_card(card_2, controller_1, location_1, index_1)


    def _on_summoning(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        self._duel.on_summoning(controller, card)


    def _on_summoned(self, packet: Packet) -> None:
        self._duel.on_summoned()


    def _on_spsummoning(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        self._duel.on_summoning(controller, card)


    def _on_spsummoned(self, packet: Packet) -> None:
        self._duel.on_spsummoned()


    def _on_chaining(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        last_chain_player: Player = packet.read_player()
        self._duel.on_chaining(last_chain_player, card)


    def _on_chain_end(self, packet: Packet) -> None:
        self._duel.on_chain_end()


    def _on_become_target(self, packet: Packet) -> None:
        for _ in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            card: Card = self._duel.get_card(controller, location, index)
            self._duel.on_become_target(card)


    def _on_draw(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        for _ in range(packet.read_int(4)):
            self._duel.on_draw(player)


    def _on_damage(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        damage: int = packet.read_int(4)
        self._duel.on_damage(player, damage)


    def _on_recover(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        recover: int = packet.read_int(4)
        self._duel.on_recover(player, recover)


    def _on_equip(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: CardPosition = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: CardPosition = packet.read_position()

        equip: Card = self._duel.get_card(controller_1, location_1, index_1)
        equipped: Card = self._duel.get_card(controller_2, location_2, index_2)

        equip.equip_target = equipped
        equipped.equip_cards.append(equip)


    def _on_unequip(self, packet: Packet) -> None:
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        equip: Card = self._duel.get_card(controller, location, index)
        equip.equip_target.equip_cards.remove(equip)
        equip.equip_target = None


    def _on_lp_update(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        lp: int = packet.read_int(4)
        self._duel.on_lp_update(player, lp)


    def _on_card_target(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: CardPosition = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: CardPosition = packet.read_position()
        targeting: Card = self._duel.get_card(controller_1, location_1, index_1)
        targeted: Card = self._duel.get_card(controller_2, location_2, index_2)
        targeting.target_cards.append(targeted)
        targeted.targeted_by.append(targeting)


    def _on_cancel_target(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: CardPosition = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: CardPosition = packet.read_position()
        targeting: Card = self._duel.get_card(controller_1, location_1, index_1)
        targeted: Card = self._duel.get_card(controller_2, location_2, index_2)
        targeting.target_cards.remove(targeted)
        targeted.targeted_by.remove(targeting)


    def _on_attack(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: CardPosition = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: CardPosition = packet.read_position()
        attacking: Card = self._duel.get_card(controller_1, location_1, index_1)
        attacked: Card = self._duel.get_card(controller_2, location_2, index_2)
        self._duel.on_attack(attacking, attacked)
        

    def _on_battle(self, packet: Packet) -> None:
        self._duel.on_battle()
    

    def _on_attack_disabled(self, packet: Packet) -> None:
        self._duel.on_battle()


    def _on_rock_paper_scissors(self, packet: Packet) -> None:
        pass


    def _on_tag_swap(self, packet: Packet) -> None:
        pass


