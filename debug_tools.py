import time
from typing import Callable, TypeVar, Any, Dict
from pyYGOclient.pyYGOnetwork.enums import CtosMessage, GameMessage, StocMessage

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
    ctsmsgs: Dict[int, CtosMessage] = {int(cts): cts for cts in CtosMessage}
    stcmsgs: Dict[int, StocMessage] = {int(stc): stc for stc in StocMessage}
    gmmsgs: Dict[int, GameMessage] = {int(gm): gm for gm in GameMessage}
    notshow_ctos: set[CtosMessage] = {CtosMessage.TIME_CONFIRM}
    notshow_stoc: set[StocMessage] = {StocMessage.TIMELIMIT}
    notshow_gm: set[GameMessage] = {}

    size = len(data)
    if send:
        if msg_id in notshow_ctos: return
        if msg_id in ctsmsgs:
            print(f'\nBot send: {size} bytes')
            print(repr(ctsmsgs[msg_id]))
            print(data.hex(' '))

    else:
        if msg_id in notshow_stoc: return
        if msg_id == StocMessage.GAME_MSG:
            gid = int.from_bytes(data[1:2], byteorder='little')
            if gid in notshow_gm: return
            print(f'\nBot received: {size} bytes')
            print(repr(stcmsgs[msg_id]))
            print(repr(gmmsgs[gid]))
            print(data.hex(' '))
        elif msg_id in stcmsgs:
            print(f'\nBot received: {size} bytes')
            print(repr(stcmsgs[msg_id]))
            print(data.hex(' '))

