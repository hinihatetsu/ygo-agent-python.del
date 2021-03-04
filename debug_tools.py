import time
from typing import Callable, TypeVar, Any
from pyYGOenvironment.pyYGOnetwork.enums import CtosMessage, GameMessage, StocMessage

T = TypeVar('T')
def measure_time(func: Callable[[Any], T]) -> Callable[[Any], T]:
    def wrapper(*args, **kwargs) -> T:
        t0 = time.time()
        result: T = func(*args, **kwargs)
        t = time.time() - t0
        print(f'{func.__name__}: {t}[s]')
        return result
    return wrapper


def print_message(msg_id: int, data: bytes, send: bool=False) -> None:
    ctsmsgs: dict[int, CtosMessage] = {int(cts): cts for cts in CtosMessage}
    stcmsgs: dict[int, StocMessage] = {int(stc): stc for stc in StocMessage}
    gmmsgs: dict[int, GameMessage] = {int(gm): gm for gm in GameMessage}
    notshow_ctos: set[CtosMessage] = {}
    notshow_stoc: set[StocMessage] = {}
    notshow_gm: set[GameMessage] = {}

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
            print(f'\nBot received: {size} bytes')
            print(repr(stcmsgs[msg_id]))
            print(repr(gmmsgs[gid]))
            print(data[1:].hex(' '))
        else:
            print(f'\nBot received: {size} bytes')
            print(repr(stcmsgs[msg_id]))
            print(data.hex(' '))

