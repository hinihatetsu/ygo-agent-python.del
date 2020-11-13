import asyncio
import random
from typing import Callable, Dict, List

from util import LaunchInfo, print_message
from pyYGO.duel import Duel
from pyYGO.card import Card
from pyYGO.zone import Zone
from pyYGO.phase import MainPhase, BattlePhase
from pyYGO.enums import Player, CardLocation, CardPosition, Attribute, Race
from pyYGO.wrapper import Location, Position 
from pyYGOAgent.agent import DuelAgent
from pyYGONetwork.network import YGOConnection
from pyYGONetwork.packet import Packet
from pyYGONetwork.enums import CtosMessage, StocMessage, GameMessage


class GameClient:
    SERVER_HANDSHAKE: int = 4043399681
    MAX_MATCH: int = 500
    def __init__(self, info: LaunchInfo) -> None:
        self.info: LaunchInfo = info
        self.connection = YGOConnection(info.host, info.port)
        self.duel: Duel = Duel()
        self.agent: DuelAgent = DuelAgent(info.deck, self.duel)

        self.responds: Dict[StocMessage, Callable] = dict()
        self.processes: Dict[GameMessage, Callable] = dict()
        self.register_responds()
        self.register_processes()

        self.select_hint: int = 0
        self.match_count: int = 0


    def start(self) -> None:
        asyncio.run(self.main())


    async def main(self) -> None:
        await self.connection.connect()
        self.on_connected()
        # concurrent tasks
        response_task: asyncio.Task = asyncio.create_task(self.main_loop())
        listen_task: asyncio.Task = asyncio.create_task(self.connection.listen())

        await response_task
        await listen_task
        

    async def main_loop(self) -> None:
        while self.connection.is_connected:
            packet: Packet = await self.connection.receive_pending_packet()
            self.on_recieved(packet)
            await self.connection.drain()


    def on_connected(self) -> None:
        packet: Packet = Packet(CtosMessage.PLAYER_INFO)
        packet.write(self.info.name, byte_size=40)
        self.connection.send(packet)

        junc = bytes([0xcc, 0xcc, 0x00, 0x00, 0x00, 0x00])
        packet = Packet(CtosMessage.JOIN_GAME)
        packet.write(self.info.version & 0xffff, byte_size=2)
        packet.write(junc)
        packet.write('', byte_size=40) # host_room_info here
        packet.write(self.info.version)
        self.connection.send(packet)


    def on_recieved(self, packet: Packet) -> None:
        if packet.msg_id == StocMessage.GAME_MSG:
            id: int = packet.read_int(1)
            if id in self.processes:
                self.processes[id](packet)

        if packet.msg_id in self.responds:
            self.responds[packet.msg_id](packet)
        

    def register_responds(self) -> None:
        self.responds[StocMessage.ERROR_MSG] = self.on_error_msg
        self.responds[StocMessage.SELECT_HAND] = self.on_select_hand
        self.responds[StocMessage.SETECT_TP] = self.on_select_tp
        self.responds[StocMessage.CHANGE_SIDE] = self.on_change_side
        self.responds[StocMessage.JOIN_GAME] = self.on_joined_game
        self.responds[StocMessage.TYPE_CHANGE] = self.on_type_changed
        self.responds[StocMessage.DUEL_END] = self.on_duel_end
        self.responds[StocMessage.REPLAY] = self.on_replay
        self.responds[StocMessage.TIMELIMIT] = self.on_timelimit
        self.responds[StocMessage.CHAT] = self.on_chat
        self.responds[StocMessage.PLAYER_ENTER] = self.on_player_enter
        self.responds[StocMessage.PLAYER_CHANGE] = self.on_player_change
        self.responds[StocMessage.REMATCH] = self.on_rematch


    def on_error_msg(self, packet: Packet) -> None:
        pass


    def on_select_hand(self, packet: Packet) -> None:
        hand: int = random.randint(1, 3)
        reply: Packet = Packet(CtosMessage.HAND_RESULT)
        reply.write(hand, byte_size=1)
        self.connection.send(reply)


    def on_select_tp(self, packet: Packet) -> None:
        select_first: bool = True
        reply: Packet = Packet(CtosMessage.TP_RESULT)
        reply.write(select_first)
        self.connection.send(reply)


    def on_change_side(self, packet: Packet) -> None:
        reply: Packet = Packet(CtosMessage.UPDATE_DECK)
        reply.write(self.agent.deck.count_main + self.agent.deck.count_extra)
        reply.write(self.agent.deck.count_side)
        for card in self.agent.deck.main + self.agent.deck.extra + self.agent.deck.side:
            reply.write(card)
        self.connection.send(reply)


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
            self.connection.close()
            return

        reply: Packet = Packet(CtosMessage.UPDATE_DECK)
        reply.write(self.agent.deck.count_main + self.agent.deck.count_extra)
        reply.write(self.agent.deck.count_side)
        for card in self.agent.deck.main + self.agent.deck.extra + self.agent.deck.side:
            reply.write(card)
        self.connection.send(reply)


    def on_type_changed(self, packet: Packet) -> None:
        is_spectator: int = 7
        position = packet.read_int(1)
        if position < 0 or position >= is_spectator:
            self.connection.close()
            return

        self.connection.send(Packet(CtosMessage.READY))


    def on_duel_end(self, packet: Packet) -> None:
        self.connection.close()


    def on_replay(self, packet: Packet) -> None:
        if self.match_count % self.agent.TRAINING_INTERVAL == 0:
            reply: Packet = Packet(CtosMessage.CHAT)
            content: str = "I'm training now. Please wait for a while."
            reply.write(content, byte_size=2*len(content))
            reply.write(0)
            self.connection.send(reply)
            self.agent.brain.train()


    def on_timelimit(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        if player == Player.ME:  
            self.connection.send(Packet(CtosMessage.TIME_CONFIRM))


    def on_chat(self, packet: Packet) -> None:
        pass


    def on_player_enter(self, packet: Packet) -> None:
        name: str = packet.read_str(40)


    def on_player_change(self, packet: Packet) -> None:
        pass


    def on_rematch(self, packet: Packet) -> None:
        ans: bool = None
        if self.match_count < self.MAX_MATCH:
            ans = True
            self.match_count += 1
        else:
            ans = False
        
        reply: Packet = Packet(CtosMessage.REMATCH_RESPONSE)
        reply.write(ans)
        self.connection.send(reply)

    
    def register_processes(self) -> None:
        self.processes[GameMessage.RETRY] = self.on_retry
        self.processes[GameMessage.HINT] = self.on_hint
        self.processes[GameMessage.START] = self.on_start
        self.processes[GameMessage.WIN] = self.on_win
        self.processes[GameMessage.UPDATE_DATA] = self.on_update_data
        self.processes[GameMessage.UPDATE_CARD] = self.on_update_card
        self.processes[GameMessage.SELECT_IDLE_CMD] = self.on_select_idle_cmd
        self.processes[GameMessage.SELECT_BATTLE_CMD] = self.on_select_battle_cmd
        self.processes[GameMessage.SELECT_EFFECT_YN] = self.on_select_effect_yn
        self.processes[GameMessage.SELECT_YESNO] = self.on_select_yesno
        self.processes[GameMessage.SELECT_OPTION] = self.on_select_option
        self.processes[GameMessage.SELECT_CARD] = self.on_select_card
        self.processes[GameMessage.SELECT_CHAIN] = self.on_select_chain
        self.processes[GameMessage.SELECT_PLACE] = self.on_select_place
        self.processes[GameMessage.SELECT_POSITION] = self.on_select_position
        self.processes[GameMessage.SELECT_TRIBUTE] = self.on_select_tribute
        self.processes[GameMessage.SELECT_COUNTER] = self.on_select_counter
        self.processes[GameMessage.SELECT_SUM] = self.on_select_sum
        self.processes[GameMessage.SELECT_DISFIELD] = self.on_select_place
        self.processes[GameMessage.SELECT_UNSELECT] = self.on_select_unselect
        self.processes[GameMessage.SHUFFLE_DECK] = self.on_shuffle_deck
        self.processes[GameMessage.SHUFFLE_HAND] = self.on_shuffle_hand
        self.processes[GameMessage.SHUFFLE_EXTRA] = self.on_shuffle_extra
        self.processes[GameMessage.SHUFFLE_SETCARD] = self.on_shuffle_setcard
        self.processes[GameMessage.SORT_CARD] = self.on_sort_card
        self.processes[GameMessage.SORT_CHAIN] = self.on_sort_chain
        self.processes[GameMessage.NEW_TURN] = self.on_new_turn
        self.processes[GameMessage.NEW_PHASE] = self.on_new_phase
        self.processes[GameMessage.MOVE] = self.on_move
        self.processes[GameMessage.POSCHANGE] = self.on_poschange
        self.processes[GameMessage.SET] = self.on_set
        self.processes[GameMessage.SWAP] = self.on_swap
        self.processes[GameMessage.SUMMONING] = self.on_summoning
        self.processes[GameMessage.SUMMONED] = self.on_summoned
        self.processes[GameMessage.SPSUMMONING] = self.on_spsummoning
        self.processes[GameMessage.SPSUMMONED] = self.on_spsummoned
        self.processes[GameMessage.FLIPSUMMONING] = self.on_summoning
        self.processes[GameMessage.FLIPSUMMONED] = self.on_summoned
        self.processes[GameMessage.CHAINING] = self.on_chaining
        self.processes[GameMessage.CHAIN_END] = self.on_chain_end
        self.processes[GameMessage.BECOME_TARGET] = self.on_become_target
        self.processes[GameMessage.DRAW] = self.on_draw
        self.processes[GameMessage.DAMAGE] = self.on_damage
        self.processes[GameMessage.RECOVER] = self.on_recover
        self.processes[GameMessage.EQUIP] = self.on_equip
        self.processes[GameMessage.UNEQUIP] = self.on_unequip
        self.processes[GameMessage.LP_UPDATE] = self.on_lp_update
        self.processes[GameMessage.CARD_TARGET] = self.on_card_target
        self.processes[GameMessage.CANCEL_TARGET] = self.on_cancel_target
        self.processes[GameMessage.PAY_LPCOST] = self.on_damage
        self.processes[GameMessage.ATTACK] = self.on_attack
        self.processes[GameMessage.BATTLE] = self.on_battle
        self.processes[GameMessage.ATTACK_DISABLED] = self.on_attack_disabled
        self.processes[GameMessage.ROCK_PAPER_SCISSORS] = self.on_rock_paper_scissors
        self.processes[GameMessage.ANNOUNCE_RACE] = self.on_announce_race
        self.processes[GameMessage.ANNOUNCE_ATTRIB] = self.on_announce_attr
        self.processes[GameMessage.ANNOUNCE_CARD] = self.on_announce_card
        self.processes[GameMessage.ANNOUNCE_NUNBER] = self.on_announce_number
        self.processes[GameMessage.TAG_SWAP] = self.on_tag_swap

    
    def on_retry(self, packet: Packet) -> None:
        # retry means we send an invalid message
        print_message(self.connection.last_recieved.msg_id, self.connection.last_recieved.content)
        print_message(self.connection.last_send.msg_id, self.connection.last_send.content, send=True)
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
                self.duel.mainphase_end = True
                
            elif data == BATTLEING:
                self.duel.field[0].under_attack = False
                self.duel.field[1].under_attack = False

        if hint_type == HINT_SELECT:
            self.select_hint = data

    
    def on_start(self, packet: Packet) -> None:
        self.agent.start_new_game()
        self.duel.__init__()
        Packet.first_is_me = not packet.read_bool()
        self.duel.first = Player.ME if Packet.first_is_me else Player.OPPONENT
        self.duel.second = Player.OPPONENT if Packet.first_is_me else Player.ME

        for player in self.duel.players:
            self.duel.life[player] = packet.read_int(4)
        
        for player in self.duel.players:
            num_of_main: int = packet.read_int(2)
            num_of_extra: int = packet.read_int(2)
            self.duel.field[player].set_deck(num_of_main, num_of_extra)
        

    def on_win(self, packet: Packet) -> None:
        print(f'Match {self.match_count}:', end='')
        print('win' if packet.read_player() == Player.ME else 'lose')
        self.agent.on_win()
        

    def on_update_data(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        location: Location = packet.read_location()

        cards: List[Card] = []
        if location.is_list:
            cards = self.duel.field[player].where(location)

        elif location.is_zone:
            zones: List[Zone] = self.duel.field[player].where(location)
            cards = [zone.card for zone in zones]

        size: int = packet.read_int(4)
        for card in cards:
            if card is not None:
                card.update(packet)
            else:
                packet.read_bytes(2) # read \x00\x00, which means no card
        

    def on_update_card(self, packet: Packet) -> None:
        player: int = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(1)

        card: Card = self.duel.field[player].get_card(location, index)
        card.update(packet)


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

                    card: Card = self.duel.field[controller].get_card(location, index)
                    card.id = card_id
                    main.activatable.append(card)
                    main.activation_descs.append(description)

            else:
                for _ in range(packet.read_int(4)):
                    card_id: int = packet.read_id()
                    controller: Player = packet.read_player()
                    location: Location = packet.read_location()
                    index: int = packet.read_int(4) if card_list is not main.repositionable else packet.read_int(1)

                    card: Card = self.duel.field[controller].get_card(location, index)
                    card.id = card_id
                    card_list.append(card)

        main.can_battle = packet.read_bool()
        main.can_end = packet.read_bool()
        can_shuffle = packet.read_bool()

        selected: int = self.agent.select_mainphase_action(main)
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self.connection.send(reply)


    def on_select_battle_cmd(self, packet:Packet) -> None:
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

            card: Card = self.duel.field[controller].get_card(location, index)
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

            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            card.can_direct_attack = direct_attackable
            card.attacked = False
            battle.attackable.append(card)

        battle.can_main2 = packet.read_bool()
        battle.can_end = packet.read_bool()

        selected: int = self.agent.select_battle_action(battle)
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self.connection.send(reply)


    def on_select_effect_yn(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        description: int = packet.read_int(8)

        card: Card = self.duel.field[controller].get_card(location, index)
        card.id = card_id
        ans: bool = self.agent.select_effect_yn(card, description)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self.connection.send(reply)


    def on_select_yesno(self, packet: Packet) -> None:
        REPLAY_BATTLE = 30
        player_msg_sent_to: int = packet.read_player()
        desc: int = packet.read_int(8)
        if desc == REPLAY_BATTLE:
            ans: bool = self.agent.select_battle_replay()
        else:
            ans: bool = self.agent.select_yn()
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self.connection.send(reply)


    def on_select_option(self, packet: Packet) -> None:
        player_msg_sent_to: int = packet.read_int(1)
        num_of_options: int = packet.read_int(1)
        options: List[int] = [packet.read_int(8) for _ in range(num_of_options)]
        ans: int = self.agent.select_option(options)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(ans)
        self.connection.send(reply)


    def on_select_card(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        cancelable: bool = packet.read_bool()
        min: int = packet.read_int(4) # min number of cards to select
        max: int = packet.read_int(4) # max number of cards to select

        choices: List[Card] = []
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            choices.append(card)

        selected: List[int] = self.agent.select_card(choices, min, max, cancelable, self.select_hint)
        self.select_hint = 0

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(0)
        reply.write(len(selected))
        for i in selected:
            reply.write(i)
        self.connection.send(reply)


    def on_select_chain(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        specount: int = packet.read_int(1)
        forced: bool = packet.read_bool()
        hint1: int = packet.read_int(4)
        hint2: int = packet.read_int(4)

        cards: List[Card] = [] # activatable cards
        descriptions: List[int] = []

        for _ in range(packet.read_int(4)):
            card_id = packet.read_int(4)
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            description: int = packet.read_int(8)
            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            card.position = position
            cards.append(card)
            descriptions.append(description)
            operation_type: bytes = packet.read_bytes(1)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        if len(cards) == 0:
            reply.write(-1)
        else:
            selected: int = self.agent.select_chain(cards, descriptions, forced)
            reply.write(selected)
        self.connection.send(reply)


    def on_select_place(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        min: int = packet.read_int(1)
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
        
        selected: int = self.agent.select_place(player, location, selectable, is_pzone)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(player)
        reply.write(int(location), byte_size=1)
        reply.write(selected, byte_size=1)
        self.connection.send(reply)


    def on_select_position(self, packet: Packet) -> None:
        player_msg_sent_to: int = packet.read_player()
        card_id: int = packet.read_id()
        selectable_position: Position = packet.read_int(1)

        POSITION: List[CardPosition] = [
            CardPosition.FASEUP_ATTACK, 
            CardPosition.FASEDOWN_ATTACK, 
            CardPosition.FASEUP_DEFENCE, 
            CardPosition.FASEDOWN_DEFENCE
        ]
        
        choices: List[CardPosition] = [pos for pos in POSITION if selectable_position & pos]
        selected: int = self.agent.select_position(card_id, choices)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self.connection.send(reply)


    def on_select_tribute(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        cancelable: bool = packet.read_bool()
        min: int = packet.read_int(4) # min number of cards to select
        max: int = packet.read_int(4) # max number of cards to select

        choices: List[Card] = []
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            packet.read_bytes(1)
            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            choices.append(card)

        selected: List[int] = self.agent.select_tribute(choices, min, max, cancelable, self.select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(0)
        reply.write(len(selected))
        for integer in selected:
            reply.write(integer)
        self.connection.send(reply)


    def on_select_counter(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        counter_type: int = packet.read_int(2)
        quantity: int = packet.read_int(4)

        cards: List[Card] = []
        counters: List[int] = []

        for _ in range(packet.read_int(1)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(1)
            num_of_counter: int = packet.read_int(2)

            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            cards.append(card)
            counters.append(num_of_counter)

        used: List[int] = self.agent.select_counter(counter_type, quantity, cards, counters)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        for i in used:
            reply.write(i & 0xff, byte_size=1)
            reply.write((i >> 8) & 0xff, byte_size=1)
        self.connection.send(reply)


    def on_select_sum(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        mode: bool = packet.read_bool()
        sum_value: int = packet.read_int(4)
        min: int = packet.read_int(4)
        max: int = packet.read_int(4)

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_int(4)
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            

        raise Exception('not complete coding')


    def on_select_unselect(self, packet: Packet) -> None:
        player_msg_snt_to: Player = packet.read_player()
        finishable: bool = packet.read_bool()
        cancelable: bool = packet.read_bool() or finishable
        min: int = packet.read_int(4)
        max: int = packet.read_int(4)

        cards: List[Card] = []

        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()

            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            card.position = position
            cards.append(card)

        # unknown  
        for _ in range(packet.read_int(4)):
            card_id: int = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()

        max = 1
        selected: List[int] = self.agent.select_unselect(cards, int(not finishable), max, cancelable, self.select_hint)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        if len(selected) == 0:
            reply.write(-1)
        else:
            reply.write(len(selected))
            for integer in selected:
                reply.write(integer)
        self.connection.send(reply)


    def on_shuffle_deck(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        for card in self.duel.field[player].deck:
            card.id = 0


    def on_shuffle_hand(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_of_hand: int = packet.read_int(4)
        for card in self.duel.field[player].hand:
            card.id = packet.read_int(4)

    
    def on_shuffle_extra(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_of_extra: int = packet.read_int(4)
        for card in self.duel.field[player].extradeck:
            if not card.is_faceup:
                card.id = packet.read_int(4)


    def on_shuffle_setcard(self, packet: Packet) -> None:
        location: Location = packet.read_location()

        old: List[Card] = []
        for _ in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = 0
            card.position = position
            old.append(card)

        for i in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            self.duel.field[controller].add_card(old[i], location, index)

    
    def on_sort_card(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        cards: List[Card] = []
        for _ in range(packet.read_int(4)):
            card_id = packet.read_id()
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            card: Card = self.duel.field[controller].get_card(location, index)
            card.id = card_id
            cards.append(card)
        
        selected: List[int] = self.agent.sort_card(cards)
        
        reply: Packet = Packet(CtosMessage.RESPONSE)
        for integer in selected:
            reply.write(integer, byte_size=1)
        self.connection.send(reply)


    def on_sort_chain(self, packet: Packet) -> None:
        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(-1)
        self.connection.send(reply)


    def on_new_turn(self, packet: Packet) -> None:
        self.duel.turn += 1
        self.duel.turn_player = packet.read_player()
        self.agent.on_new_turn()


    def on_new_phase(self, packet: Packet) -> None:
        self.duel.phase = packet.read_phase()
        for player in self.duel.players:
            self.duel.field[player].battling_monster = None
            self.duel.field[player].under_attack = False

        for monster in self.duel.field[0].get_monsters():
            monster.attacked = False

        self.duel.mainphase_end = False


    def on_move(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        # p means previous, c means current
        p_controller: Player = packet.read_player()
        p_location: Location = packet.read_location()
        p_index: int = packet.read_int(4)
        p_position: Position = packet.read_position()
        c_controller: Player = packet.read_player()
        c_location: Location = packet.read_location()
        c_index: int = packet.read_int(4)
        c_position: Position = packet.read_position()
        reason: int = packet.read_int(4)

        card: Card = self.duel.field[p_controller].get_card(p_location, p_index)
        self.duel.field[p_controller].remove_card(card, p_location, p_index)
        card.id = card_id
        card.controller = c_controller
        card.location = c_location
        card.position = c_position
        self.duel.field[c_controller].add_card(card, c_location, c_index)


    def on_poschange(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        # p means previous, c means current
        p_controller: Player = packet.read_player()
        p_location: Location = packet.read_location()
        p_index: int = packet.read_int(1)
        p_position: int = packet.read_int(1)
        c_position: int = packet.read_int(1)

        card: Card = self.duel.field[p_controller].get_card(p_location, p_index)
        card.position = c_position


    def on_set(self, packet: Packet) -> None:
        pass


    def on_swap(self, packet: Packet) -> None:
        # p means previous, c means current
        card_id_1: int = packet.read_id()
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: Position = packet.read_position()
        card_id_2: int = packet.read_id()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: Position = packet.read_position()

        card_1: Card = self.duel.field[controller_1].get_card(location_1, index_1)
        card_1.id = card_id_1
        card_2: Card = self.duel.field[controller_2].get_card(location_2, index_2)
        card_2.id = card_id_2

        self.duel.field[controller_1].remove_card(card_1, location_1, index_1)
        self.duel.field[controller_2].remove_card(card_2, location_2, index_2)
        self.duel.field[controller_1].add_card(card_1, location_2, index_2)
        self.duel.field[controller_2].add_card(card_2, location_1, index_1)


    def on_summoning(self, packet: Packet) -> None:
        self.duel.summoning.clear()
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        card: Card = self.duel.field[controller].get_card(location, index)
        card.id = card_id
        self.duel.summoning.append(card)
        self.duel.last_summon_player = controller


    def on_summoned(self, packet: Packet) -> None:
        self.duel.last_summoned = [card for card in self.duel.summoning]
        self.duel.summoning.clear()


    def on_spsummoning(self, packet: Packet) -> None:
        self.duel.last_summoned.clear()
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        card: Card = self.duel.field[controller].get_card(location, index)
        card.id = card_id
        self.duel.summoning.append(card)
        self.duel.last_summon_player = controller


    def on_spsummoned(self, packet: Packet) -> None:
        self.duel.last_summoned = [card for card in self.duel.summoning]
        for card in self.duel.last_summoned:
            card.is_special_summoned = True
        self.duel.summoning.clear()


    def on_chaining(self, packet: Packet) -> None:
        card_id: int = packet.read_id()
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        card: Card = self.duel.field[controller].get_card(location, index)
        card.id = card_id
        self.duel.last_chain_player = packet.read_player()
        self.duel.last_summon_player = None
        self.duel.current_chain.append(card)
        self.duel.current_chain_target.clear()


    def on_chain_end(self, packet: Packet) -> None:
        self.duel.mainphase_end = False
        self.duel.last_chain_player = -1
        self.duel.current_chain.clear()
        self.duel.chain_targets.clear()
        self.duel.current_chain_target.clear()


    def on_become_target(self, packet: Packet) -> None:
        for _ in range(packet.read_int(4)):
            controller: Player = packet.read_player()
            location: Location = packet.read_location()
            index: int = packet.read_int(4)
            position: Position = packet.read_position()
            card: Card = self.duel.field[controller].get_card(location, index)
            self.duel.chain_targets.append(card)
            self.duel.current_chain_target.append(card)


    def on_draw(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        num_to_draw: int = packet.read_int(4)

        for _ in range(num_to_draw):
            self.duel.field[player].deck.pop()
            self.duel.field[player].hand.append(Card(location=CardLocation.HAND))


    def on_damage(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        self.duel.life[player] = max(self.duel.life[player] - packet.read_int(4), 0)


    def on_recover(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        self.duel.life[player] += packet.read_int(4)


    def on_equip(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: Position = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: Position = packet.read_position()

        equip: Card = self.duel.field[controller_1].get_card(location_1, index_1)
        equipped: Card = self.duel.field[controller_2].get_card(location_2, index_2)

        equip.equip_target = equipped
        equipped.equip_cards.append(equip)


    def on_unequip(self, packet: Packet) -> None:
        controller: Player = packet.read_player()
        location: Location = packet.read_location()
        index: int = packet.read_int(4)
        position: Position = packet.read_position()
        equip: Card = self.duel.field[controller].get_card(location, index)
        equip.equip_target.equip_cards.remove(equip)
        equip.equip_target = None


    def on_lp_update(self, packet: Packet) -> None:
        player: Player = packet.read_player()
        self.duel.life[player] = packet.read_int(4)


    def on_card_target(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: Position = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: Position = packet.read_position()
        targeting: Card = self.duel.field[controller_1].get_card(location_1, index_1)
        targeted: Card = self.duel.field[controller_2].get_card(location_2, index_2)
        targeting.target_cards.append(targeted)
        targeted.targeted_by.append(targeting)


    def on_cancel_target(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: Position = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: Position = packet.read_position()
        targeting: Card = self.duel.field[controller_1].get_card(location_1, index_1)
        targeted: Card = self.duel.field[controller_2].get_card(location_2, index_2)
        targeting.target_cards.remove(targeted)
        targeted.targeted_by.remove(targeting)


    def on_attack(self, packet: Packet) -> None:
        controller_1: Player = packet.read_player()
        location_1: Location = packet.read_location()
        index_1: int = packet.read_int(4)
        position_1: Position = packet.read_position()
        controller_2: Player = packet.read_player()
        location_2: Location = packet.read_location()
        index_2: int = packet.read_int(4)
        position_2: Position = packet.read_position()
        attack: Card = self.duel.field[controller_1].get_card(location_1, index_1)
        attacked: Card = self.duel.field[controller_2].get_card(location_2, index_2)
        self.duel.field[attack.controller].battling_monster = attack
        self.duel.field[attack.controller ^ 1].battling_monster = attacked
        self.duel.field[attack.controller ^ 1].under_attack = True
        

    def on_battle(self, packet: Packet) -> None:
        self.duel.field[Player.ME].under_attack = False
        self.duel.field[Player.OPPONENT].under_attack = False


    def on_attack_disabled(self, packet: Packet) -> None:
        self.duel.field[Player.ME].under_attack = False
        self.duel.field[Player.OPPONENT].under_attack = False


    def on_rock_paper_scissors(self, packet: Packet) -> None:
        pass


    def on_announce_race(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        available: int = packet.read_int(4)
        choices: List[Race] = []
        for race in Race:
            if available & race:
                choices.append(race)

        selected: List[int] = self.agent.announce_race(choices, count)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(sum(selected))
        self.connection.send(reply)


    def on_announce_card(self, packet: Packet) -> None:
        raise Exception('not complete coding')


    def on_announce_attr(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        available: int = packet.read_int(4)
        choices: List[Attribute] = []
        for attr in Attribute:
            if available & attr:
                choices.append(attr)

        selected: List[int] = self.agent.announce_attr(choices, count)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(sum(selected))
        self.connection.send(reply)


    def on_announce_number(self, packet: Packet) -> None:
        player_msg_sent_to: Player = packet.read_player()
        count: int = packet.read_int(1)
        choices: List[int] = [packet.read_int(4) for _ in range(count)]
        selected: int = self.agent.select_number(choices)

        reply: Packet = Packet(CtosMessage.RESPONSE)
        reply.write(selected)
        self.connection.send(reply)


    def on_tag_swap(self, packet: Packet) -> None:
        pass

    
