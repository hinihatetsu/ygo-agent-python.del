from pathlib import Path
import sqlite3
from typing import NamedTuple, List, Dict, Any
from pyYGONetwork.enums import CtosMessage, GameMessage, StocMessage


class LaunchInfo(NamedTuple):
    name: str = 'AI'
    deck: str = ''
    host: str = '127.0.0.1'
    port: int = 7911
    version: int = 38 | 1<<8 | 8<<16


def load_args(args: List[str]) -> LaunchInfo:
    info: Dict[str, Any] = dict()
    for arg in args:
        equal_index: int = arg.find('=')
        if equal_index == (-1 or len(arg)-1):
            continue

        key: str = arg[:equal_index].lower()
        if key in {'name', 'deck', 'host'}:
            info[key] = arg[equal_index+1:]
        elif key in {'port', 'version'}:
            info[key] = int(arg[equal_index+1:])
    
    return LaunchInfo(**info)


def print_message(msg_id: bytes, data: bytes, send: bool=False) -> None:
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



def print_description(card_id: int, desc: int) -> None: 
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
