from typing import Dict, TypeVar

from pyYGO.enums import Player, CardLocation, CardPosition, Phase
from pyYGO.alias import Location, LocationInfo, Position

Message = TypeVar('Message', Player, str, int, bytes, bytearray, bool)

class Packet:
    first_is_me: bool
    LOCATION: Dict[int, CardLocation] = {int(loc): loc for loc in CardLocation}
    POSITION: Dict[int, CardPosition] = {int(pos): pos for pos in CardPosition}
    PHASE: Dict[int, Phase] = {int(phase): phase for phase in Phase}
    
    def __init__(self, msg_id: int=None):
        self._msg_id: bytes = b'' # _msg_id is 'bytes', msg_id is 'int'
        self.content: bytes = b''
        self._position: int = 0
        if msg_id is not None:
            self.msg_id = msg_id
    
    @property
    def msg_id(self) -> int:
        return int.from_bytes(self._msg_id, byteorder="little")

    @msg_id.setter
    def msg_id(self, msg_id: int) -> None:
        self._msg_id = msg_id.to_bytes(1, byteorder='little')

    def __repr__(self) -> str:
        return f'<msg_id: {self.msg_id}>' + self.content.hex(' ')


    def write(self, content: Message, * , byte_size: int=4) -> None:
        _type: type = type(content)

        if _type == Player:
            self.write(int(content) if self.first_is_me else int(content ^ 1), byte_size=1)

        elif _type == str:
            content = str(content)
            encoded = content.encode(encoding='utf-16-le')
            max_size = byte_size - 2
            if len(encoded) <= max_size:
                self.content += encoded + bytes(byte_size-len(encoded))
            else:
                self.content += encoded[:max_size] + bytes(2)
        
        elif _type == int:
            content = int(content)
            if content < 0:
                content += 1 << (byte_size * 8)
            self.content += content.to_bytes(byte_size, byteorder='little')

        elif _type == bytes:
            self.content += content
        
        elif _type == bytearray:
            self.content += bytes(content)

        elif _type == bool:
            self.content += int(content).to_bytes(1, byteorder='little')
            
    
    def read_bytes(self, byte: int) -> bytes:
        res: bytes = self.content[self._position:self._position+byte]
        self._position += byte
        return res


    def read_int(self, byte: int) -> int:
        return int.from_bytes(self.read_bytes(byte), byteorder='little')


    def read_bool(self) -> bool:
        return bool(self.read_int(1))


    def read_str(self, byte: int) -> str:
        try:
            return self.read_bytes(byte).decode(encoding='utf-16-le')
        except UnicodeDecodeError:
            return ''


    def read_player(self) -> Player:
        if self.first_is_me ^ (self.read_int(1) == 1):
            return Player.ME
        else:
            return Player.OPPONENT


    def read_id(self) -> int:
        return self.read_int(4)


    def read_location(self) -> Location:
        loc: int = self.read_int(1)
        return self.LOCATION[loc] if loc in self.LOCATION else loc


    def read_position(self) -> Position:
        pos: int = self.read_int(4)
        return self.POSITION[pos] if pos in self.POSITION else pos


    def read_location_info(self, *, include_pos: bool=True) -> LocationInfo:
        controler = self.read_player()
        location = self.read_location()
        index = self.read_int(4)
        position = self.read_position() if include_pos else 0
        return LocationInfo(controler, location, index, position)


    def read_phase(self) -> Phase:
        phase: int = self.read_int(4)
        return self.PHASE[phase]


    


