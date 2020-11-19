import argparse
from argparse import Namespace
from pathlib import Path
import sqlite3
from typing import NamedTuple, NoReturn
from pyYGONetwork.enums import CtosMessage, GameMessage, StocMessage

VERSION: int = 38 | 1<<8 | 8<<16
class LaunchInfo(NamedTuple):
    name: str
    deck: str
    host: str
    port: int
    version: int


def load_args() -> LaunchInfo:
    parser = argparse.ArgumentParser()
    parser.set_defaults(name='AI', host='127.0.0.1', port=7911, version=VERSION)
    parser.add_argument('-name', type=str, help="AI's name (default: %(default)s)")
    parser.add_argument('-deck', type=str, help='deck name', required=True)
    parser.add_argument('-host', type=str, help='host adress (default: %(default)s)')
    parser.add_argument('-port', type=int, help='port (default: %(default)s)')
    parser.add_argument('-version', type=int, help='version (default: %(default)s)')
    args: Namespace = parser.parse_args()
    return LaunchInfo(args.name, args.deck, args.host, args.port, args.version)


def print_message(msg_id: bytes, data: bytes, send: bool=False) -> NoReturn:
    ctsmsgs = {int(cts): cts for cts in CtosMessage}
    stcmsgs = {int(stc): stc for stc in StocMessage}
    gmmsgs = {int(gm): gm for gm in GameMessage}
    notshow_ctos = {}
    notshow_stoc = {}
    notshow_gm = {}

    size = len(data)
    if send:
        if msg_id in notshow_ctos: return
        print(f'\nBot send: {size} bytes')
        print(repr(ctsmsgs[msg_id]))
        print(data.hex(' '))

    else:
        if msg_id in notshow_stoc: return
        if msg_id == StocMessage.GAME_MSG:
            gid = int.from_bytes(data[0:1], byteorder='little')
            if gid in notshow_gm: return
            print(f'\nBot recieved: {size} bytes')
            print(repr(stcmsgs[msg_id]))
            print(repr(gmmsgs[gid]))
            print(data[1:].hex(' '))
        else:
            print(f'\nBot recieved: {size} bytes')
            print(repr(stcmsgs[msg_id]))
            print(data.hex(' '))



def print_description(card_id: int, desc: int) -> NoReturn: 
    db_path = Path.cwd() / 'cards.cdb'
    db_conn = sqlite3.connect(db_path)
    cur = db_conn.cursor()
    cur.execute('select name from texts where id = ?', (card_id, ))
    card_name = cur.fetchone()[0]
    db_conn.close()
    print('\n', 'name:', card_name, '| id:', card_id)
    print('description:', desc, )
    print('>>20:', desc >> 20, '| & 0xfffff:', desc & 0xfffff)



if __name__ == '__main__':
    pass
