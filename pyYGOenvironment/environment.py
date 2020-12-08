import asyncio

import random
from collections.abc import Coroutine
from typing import Callable

from pyYGO import Duel, Card, Zone, Location
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import Phase, Player, CardLocation, CardPosition, CardType, Attribute, Query, Race
from pyYGO.deck import Deck
from .player import GamePlayer
from .pyYGOnetwork import YGOConnection, Packet, CtosMessage, StocMessage, GameMessage
from debug_tool import print_message


class GameClient:
    SERVER_HANDSHAKE: int = 4043399681
    def __init__(self, host: str, port: int, version: int, name: str) -> None:
        self._connection: YGOConnection = YGOConnection(host, port)
        self._version: int = version
        self._name: str = name
        self._duel: Duel = Duel()
        self._gameplayer: GamePlayer = None
        self._deck: Deck = None

        self._responds: dict[StocMessage, Callable] = dict()
        self._processes: dict[GameMessage, Callable] = dict()
        self._register_responds()
        self._register_processes()

        self._select_hint: int = 0
        self._best_of: int = 0
        self._win: int = 0


    def get_duel(self) -> Duel:
        return self._duel


    def set_gameplayer(self, gameplayer: GamePlayer) -> None:
        self._gameplayer = gameplayer


    def set_deck(self, deck: Deck) -> None:
        self._deck = deck


    def start(self) -> None:
        if self._gameplayer is None:
            raise Exception('GamePlayer not set. Call GameClient.set_gameplayer().')
        if self._deck is None:
            raise Exception('Deck not set. Call GameClient.set_deck().')
        asyncio.run(self._main())


    async def _main(self) -> Coroutine[None, None, None]:
        await self._connection.connect()
        if self._connection.is_connected:
            self.on_connected()
        # concurrent tasks
        response_task: asyncio.Task = asyncio.create_task(self._main_loop())
        listen_task: asyncio.Task = asyncio.create_task(self._connection.listen())

        await response_task
        await listen_task
        

    async def _main_loop(self) -> Coroutine[None, None, None]:
        while self._connection.is_connected:
            packet: Packet = await self._connection.receive_pending_packet()
            self.on_recieved(packet)
            await self._connection.drain()
        self._gameplayer.on_client_close()

    
    def chat(self, content: str) -> None:
        reply: Packet = Packet(CtosMessage.CHAT)
        reply.write(content, byte_size=2*len(content))
        reply.write(0)
        self._connection.send(reply)


    def on_connected(self) -> None:          
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


    def on_recieved(self, packet: Packet) -> None:
        if packet.msg_id == StocMessage.GAME_MSG:
            id: int = packet.read_int(1)
            if id in self._processes:
                self._processes[id](packet)

        if packet.msg_id in self._responds:
            self._responds[packet.msg_id](packet)
        

    def _register_responds(self) -> None:
        self._responds[StocMessage.ERROR_MSG] = self.on_error_msg
        self._responds[StocMessage.SELECT_HAND] = self.on_select_hand
        self._responds[StocMessage.SETECT_TP] = self.on_select_tp
        self._responds[StocMessage.CHANGE_SIDE] = self.on_change_side
        self._responds[StocMessage.JOIN_GAME] = self.on_joined_game
        self._responds[StocMessage.TYPE_CHANGE] = self.on_type_changed
        self._responds[StocMessage.DUEL_END] = self.on_duel_end
        self._responds[StocMessage.REPLAY] = self.on_replay
        self._responds[StocMessage.TIMELIMIT] = self.on_timelimit
        self._responds[StocMessage.CHAT] = self.on_chat
        self._responds[StocMessage.PLAYER_ENTER] = self.on_player_enter
        self._responds[StocMessage.PLAYER_CHANGE] = self.on_player_change
        self._responds[StocMessage.REMATCH] = self.on_rematch


    def on_error_msg(self, packet: Packet) -> None:
        pass


    def on_select_hand(self, packet: Packet) -> None:
        hand: int = random.randint(1, 3)
        reply: Packet = Packet(CtosMessage.HAND_RESULT)
        reply.write(hand, byte_size=1)
        self._connection.send(reply)


    def on_select_tp(self, packet: Packet) -> None:
        select_first: bool = False
        reply: Packet = Packet(CtosMessage.TP_RESULT)
        reply.write(select_first)
        self._connection.send(reply)


    def on_change_side(self, packet: Packet) -> None:
        reply: Packet = Packet(CtosMessage.UPDATE_DECK)
        reply.write(self._deck.count_main + self._deck.count_extra)
        reply.write(self._deck.count_side)
        for card in self._deck.main + self._deck.extra + self._deck.side:
            reply.write(card)
        self._connection.send(reply)


    def on_joined_game(self, packet: Packet) -> None:
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


    def on_type_changed(self, packet: Packet) -> None:
        is_spectator: int = 7
        position = packet.read_int(1)
        if position < 0 or position >= is_spectator:
            self._connection.close()
            return

        self._connection.send(Packet(CtosMessage.READY))
        return


    def on_duel_end(self, packet: Packet) -> None:
        self._connection.close()


    def on_replay(self, packet: Packet) -> None:
        pass


    def on_timelimit(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        if player == Player.ME:  
            self._connection.send(Packet(CtosMessage.TIME_CONFIRM))


    def on_chat(self, packet: Packet) -> None:
        pass


    def on_player_enter(self, packet: Packet) -> None:
        name: str = packet.read_str(40)


    def on_player_change(self, packet: Packet) -> None:
        pass


    def on_rematch(self, packet: Packet) -> None:
        win: bool = (2 * self._win > self._best_of)
        ans: bool = self._gameplayer.on_rematch(win)
        self._win = 0 
        reply: Packet = Packet(CtosMessage.REMATCH_RESPONSE)
        reply.write(ans)
        self._connection.send(reply)

    
    def _register_processes(self) -> None:
        self._processes[GameMessage.RETRY] = self.on_retry
        self._processes[GameMessage.HINT] = self.on_hint
        self._processes[GameMessage.START] = self.on_start
        self._processes[GameMessage.WIN] = self.on_win
        self._processes[GameMessage.UPDATE_DATA] = self.on_update_data
        self._processes[GameMessage.UPDATE_CARD] = self.on_update_card
        self._processes[GameMessage.SELECT_IDLE_CMD] = self.on_select_idle_cmd
        self._processes[GameMessage.SELECT_BATTLE_CMD] = self.on_select_battle_cmd
        self._processes[GameMessage.SELECT_EFFECT_YN] = self.on_select_effect_yn
        self._processes[GameMessage.SELECT_YESNO] = self.on_select_yesno
        self._processes[GameMessage.SELECT_OPTION] = self.on_select_option
        self._processes[GameMessage.SELECT_CARD] = self.on_select_card
        self._processes[GameMessage.SELECT_CHAIN] = self.on_select_chain
        self._processes[GameMessage.SELECT_PLACE] = self.on_select_place
        self._processes[GameMessage.SELECT_POSITION] = self.on_select_position
        self._processes[GameMessage.SELECT_TRIBUTE] = self.on_select_tribute
        self._processes[GameMessage.SELECT_COUNTER] = self.on_select_counter
        self._processes[GameMessage.SELECT_SUM] = self.on_select_sum
        self._processes[GameMessage.SELECT_DISFIELD] = self.on_select_place
        self._processes[GameMessage.SELECT_UNSELECT] = self.on_select_unselect
        self._processes[GameMessage.SHUFFLE_DECK] = self.on_shuffle_deck
        self._processes[GameMessage.SHUFFLE_HAND] = self.on_shuffle_hand
        self._processes[GameMessage.SHUFFLE_EXTRA] = self.on_shuffle_extra
        self._processes[GameMessage.SHUFFLE_SETCARD] = self.on_shuffle_setcard
        self._processes[GameMessage.SORT_CARD] = self.on_sort_card
        self._processes[GameMessage.SORT_CHAIN] = self.on_sort_chain
        self._processes[GameMessage.NEW_TURN] = self.on_new_turn
        self._processes[GameMessage.NEW_PHASE] = self.on_new_phase
        self._processes[GameMessage.MOVE] = self.on_move
        self._processes[GameMessage.POSCHANGE] = self.on_poschange
        self._processes[GameMessage.SET] = self.on_set
        self._processes[GameMessage.SWAP] = self.on_swap
        self._processes[GameMessage.SUMMONING] = self.on_summoning
        self._processes[GameMessage.SUMMONED] = self.on_summoned
        self._processes[GameMessage.SPSUMMONING] = self.on_spsummoning
        self._processes[GameMessage.SPSUMMONED] = self.on_spsummoned
        self._processes[GameMessage.FLIPSUMMONING] = self.on_summoning
        self._processes[GameMessage.FLIPSUMMONED] = self.on_summoned
        self._processes[GameMessage.CHAINING] = self.on_chaining
        self._processes[GameMessage.CHAIN_END] = self.on_chain_end
        self._processes[GameMessage.BECOME_TARGET] = self.on_become_target
        self._processes[GameMessage.DRAW] = self.on_draw
        self._processes[GameMessage.DAMAGE] = self.on_damage
        self._processes[GameMessage.RECOVER] = self.on_recover
        self._processes[GameMessage.EQUIP] = self.on_equip
        self._processes[GameMessage.UNEQUIP] = self.on_unequip
        self._processes[GameMessage.LP_UPDATE] = self.on_lp_update
        self._processes[GameMessage.CARD_TARGET] = self.on_card_target
        self._processes[GameMessage.CANCEL_TARGET] = self.on_cancel_target
        self._processes[GameMessage.PAY_LPCOST] = self.on_damage
        self._processes[GameMessage.ATTACK] = self.on_attack
        self._processes[GameMessage.BATTLE] = self.on_battle
        self._processes[GameMessage.ATTACK_DISABLED] = self.on_attack_disabled
        self._processes[GameMessage.ROCK_PAPER_SCISSORS] = self.on_rock_paper_scissors
        self._processes[GameMessage.ANNOUNCE_RACE] = self.on_announce_race
        self._processes[GameMessage.ANNOUNCE_ATTRIB] = self.on_announce_attr
        self._processes[GameMessage.ANNOUNCE_CARD] = self.on_announce_card
        self._processes[GameMessage.ANNOUNCE_NUNBER] = self.on_announce_number
        self._processes[GameMessage.TAG_SWAP] = self.on_tag_swap

    
    def on_retry(self, packet: Packet) -> None:
        # retry means we send an invalid message
        print_message(self._connection.last_recieved.msg_id, self._connection.last_recieved.content)
        print_message(self._connection.last_send.msg_id, self._connection.last_send.content, send=True)
        raise Exception('sent invalid message')


    def on_hint(self, packet: Packet) -> None:
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
            self.select_hint = data

    
    def on_start(self, packet: Packet) -> None:
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
        

    def on_win(self, packet: Packet) -> None:
        win: bool = packet.read_player() == Player.ME
        if win:
            self._win += 1
        self._gameplayer.on_win(win)
        

    def on_update_data(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        location: Location = packet.read_location()
        cards: list[Card] = self._duel.get_cards(player, location)
        size: int = packet.read_int(4)
        for card in cards:
            if card is not None:
                self.update_card(card, packet)
            else:
                packet.read_bytes(2) # read \x00\x00, which means no card
        

    def on_update_card(self, packet: Packet) -> None:
        player: int = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(1)

        card: Card = self._duel.get_card(player, location, index)
        self.update_card(card, packet)

    
    def update_card(self, card: Card, packet: Packet) -> None:
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
                self.rank = packet.read_int(4)

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




    def on_select_idle_cmd(self, packet: Packet) -> None:
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


    def on_select_battle_cmd(self, packet: Packet) -> None:
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


    def on_select_effect_yn(self, packet: Packet) -> None:
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


    def on_select_yesno(self, packet: Packet) -> None:
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


    def on_select_option(self, packet: Packet) -> None:
        player_msg_sent_to: int = packet.read_int(1)
        num_of_options: int = packet.read_int(1)
        options: list[int] = [packet.read_int(8) for _ in range(num_of_options)]
        ans: int = self._gameplayer.select_option(options)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self._connection.send(reply)


    def on_select_card(self, packet: Packet) -> None:
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

        selected: list[int] = self._gameplayer.select_card(choices, min_, max_, cancelable, self.select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(0)
        reply.write(len(selected))
        for i in selected:
            reply.write(i)
        self._connection.send(reply)


    def on_select_chain(self, packet: Packet) -> None:
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


    def on_select_place(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        min_: int = packet.read_int(1)
        selectable: int = 0xffffffff - packet.read_int(4)

        player: Player = None
        location: Location = None
        is_pzone: bool = bool(selectable & (Zone.ID.PZONE | (Zone.ID.PZONE << Zone.ID.OPPONENT)))
        if selectable & Zone.ID.MONSTER_ZONE:
            player = Player.ME
            location = CardLocation.MONSTER_ZONE

        elif selectable & Zone.ID.SPELL_ZONE:
            player = Player.ME
            location = CardLocation.SPELL_ZONE

        elif selectable & (Zone.ID.MONSTER_ZONE << Zone.ID.OPPONENT):
            player = Player.OPPONENT
            location = CardLocation.MONSTER_ZONE

        elif selectable & (Zone.ID.SPELL_ZONE << Zone.ID.OPPONENT):
            player = Player.OPPONENT
            location = CardLocation.SPELL_ZONE
        
        selected: int = self._gameplayer.select_place(player, location, selectable, is_pzone)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(player)
        reply.write(int(location), byte_size=1)
        reply.write(selected, byte_size=1)
        self._connection.send(reply)


    def on_select_position(self, packet: Packet) -> None:
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


    def on_select_tribute(self, packet: Packet) -> None:
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

        selected: list[int] = self._gameplayer.select_tribute(choices, min_, max_, cancelable, self.select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(0)
        reply.write(len(selected))
        for integer in selected:
            reply.write(integer)
        self._connection.send(reply)


    def on_select_counter(self, packet: Packet) -> None:
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


    def on_select_sum(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        must_just: bool = not packet.read_bool()
        sum_value: int = packet.read_int(4)
        min_: int = packet.read_int(4)
        max_: int = packet.read_int(4)

        must_selected: list[Card] = []
        choices: list[Card] = []

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            values: tuple(int, int) = (packet.read_int(2), packet.read_int(2))
            must_selected.append(card)
            sum_value -= max(values)

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self._duel.get_card(controller, location, index)
            card.id = card_id
            values: tuple(int, int) = (packet.read_int(2), packet.read_int(2))
            choices.append((card, values))

        selected: list[int] = self._gameplayer.select_sum(choices, sum_value, min_, max_, must_just, self.select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(b'\x00\x01\x00\x00')
        reply.write(len(must_selected)+len(selected), byte_size=4)
        for _ in must_selected:
            packet.write(0, byte_size=1)
        for i in selected:
            packet.write(i, byte_size=1)
        self._connection.send(reply)


    def on_select_unselect(self, packet: Packet) -> None:
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
        selected: list[int] = self._gameplayer.select_unselect(cards, int(not finishable), max, cancelable, self.select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        if len(selected) == 0:
            reply.write(-1)
        else:
            reply.write(len(selected))
            for integer in selected:
                reply.write(integer)
        self._connection.send(reply)


    def on_shuffle_deck(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        for card in self._duel.field[player].deck:
            card.id = 0


    def on_shuffle_hand(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_of_hand: int = packet.read_int(4)
        for card in self._duel.field[player].hand:
            card.id = packet.read_int(4)

    
    def on_shuffle_extra(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_of_extra: int = packet.read_int(4)
        for card in self._duel.field[player].extradeck:
            if not card.is_faceup:
                card.id = packet.read_int(4)


    def on_shuffle_setcard(self, packet: Packet) -> None:
        location: Location = packet.read_location()

        old: list[Card] = []
        for _ in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            card: Card = self._duel.get_card(controller, location, index)
            card.id = 0
            old.append(card)

        for i in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            self._duel.add_card(old[i], controller, location, index)

    
    def on_sort_card(self, packet: Packet) -> None:
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


    def on_sort_chain(self, packet: Packet) -> None:
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(-1)
        self._connection.send(reply)


    def on_new_turn(self, packet: Packet) -> None:
        turn_player: Player = packet.read_player()
        self._duel.on_new_turn(turn_player)
        self._gameplayer.on_new_turn()


    def on_new_phase(self, packet: Packet) -> None:
        phase: Phase = packet.read_phase()
        self._duel.on_new_phase(phase)


    def on_move(self, packet: Packet) -> None:
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


    def on_poschange(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        # p means previous, c means current
        p_controller: Player = packet.read_player()
        p_location: Location = packet.read_location()
        p_index: int = packet.read_int(1)
        p_position: int = packet.read_int(1)
        c_position: int = packet.read_int(1)

        card: Card = self._duel.get_card(p_controller, p_location, p_index)
        card.position = c_position


    def on_set(self, packet: Packet) -> None:
        pass


    def on_swap(self, packet: Packet) -> None:
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


    def on_summoning(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        self._duel.on_summoning(controller, card)


    def on_summoned(self, packet: Packet) -> None:
        self._duel.on_summoned()


    def on_spsummoning(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        self._duel.on_summoning(controller, card)


    def on_spsummoned(self, packet: Packet) -> None:
        self._duel.on_spsummoned()


    def on_chaining(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        card: Card = self._duel.get_card(controller, location, index)
        card.id = card_id
        last_chain_player: Player = packet.read_player()
        self._duel.on_chaining(last_chain_player, card)


    def on_chain_end(self, packet: Packet) -> None:
        self._duel.on_chain_end()


    def on_become_target(self, packet: Packet) -> None:
        for _ in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: CardPosition = packet.read_position()
            card: Card = self._duel.get_card(controller, location, index)
            self._duel.on_become_target(card)


    def on_draw(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        for _ in range(packet.read_int(4)):
            self._duel.on_draw(player)


    def on_damage(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        damage: int = packet.read_int(4)
        self._duel.on_damage(player, damage)


    def on_recover(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        recover: int = packet.read_int(4)
        self._duel.on_recover(player, recover)


    def on_equip(self, packet: Packet) -> None:
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


    def on_unequip(self, packet: Packet) -> None:
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: CardPosition = packet.read_position()
        equip: Card = self._duel.get_card(controller, location, index)
        equip.equip_target.equip_cards.remove(equip)
        equip.equip_target = None


    def on_lp_update(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        lp: int = packet.read_int(4)
        self._duel.on_lp_update(player, lp)


    def on_card_target(self, packet: Packet) -> None:
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


    def on_cancel_target(self, packet: Packet) -> None:
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


    def on_attack(self, packet: Packet) -> None:
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
        

    def on_battle(self, packet: Packet) -> None:
        self._duel.on_battle()
    

    def on_attack_disabled(self, packet: Packet) -> None:
        self._duel.on_battle()


    def on_rock_paper_scissors(self, packet: Packet) -> None:
        pass


    def on_announce_race(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        available: int = packet.read_int(4)
        choices: list[Race] = [race for race in Race if available & race]

        selected: list[int] = self._gameplayer.announce_race(choices, count)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(sum(selected))
        self._connection.send(reply)


    def on_announce_card(self, packet: Packet) -> None:
        raise Exception('not complete coding')


    def on_announce_attr(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        available: int = packet.read_int(4)
        choices: list[Attribute] = [attr for attr in Attribute if available & attr]

        selected: list[int] = self._gameplayer.announce_attr(choices, count)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(sum(selected))
        self._connection.send(reply)


    def on_announce_number(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        choices: list[int] = [packet.read_int(4) for _ in range(count)]
        selected: int = self._gameplayer.select_number(choices)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self._connection.send(reply)


    def on_tag_swap(self, packet: Packet) -> None:
        pass


