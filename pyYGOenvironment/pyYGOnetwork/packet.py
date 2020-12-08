from typing import Union

from pyYGO.enums import Player, Phase, CardPosition
from pyYGO.wrapper import Location


class Packet:
    first_is_me: bool  
    def __init__(self, msg_id: int=None):
        self._msg_id_bytes: bytes = b'' 
        self._content: bytes = b''
        self._position: int = 0
        if msg_id is not None:
            self.msg_id = msg_id
    
    @property
    def msg_id(self) -> int:
        return int.from_bytes(self._msg_id_bytes, byteorder="little")

    @msg_id.setter
    def msg_id(self, msg_id: int) -> None:
        self._msg_id_bytes = msg_id.to_bytes(1, byteorder='little')

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def data(self) -> bytes:
        return self._msg_id_bytes + self._content


    def write(self, content: Union[str, int, bytes, bytearray, bool, Player], * , byte_size: int=4) -> None:
        type_: type = type(content)

        if type_ == Player:
            self.write(int(content) if self.first_is_me else int(content ^ 1), byte_size=1)

        elif type_ == str:
            content = str(content)
            encoded = content.encode(encoding='utf-16-le')
            if len(encoded) <= byte_size:
                self._content += encoded + bytes(byte_size-len(encoded))
            else:
                self._content += encoded[:byte_size]
        
        elif type_ == int:
            content = int(content)
            if content < 0:
                content += 1 << (byte_size * 8)
            self._content += content.to_bytes(byte_size, byteorder='little')

        elif type_ == bytes:
            self._content += content
        
        elif type_ == bytearray:
            self._content += bytes(content)

        elif type_ == bool:
            self._content += int(content).to_bytes(1, byteorder='little')

        else:
            raise ValueError('invalid type')
            
    
    def read_bytes(self, byte: int) -> bytes:
        res: bytes = self._content[self._position:self._position+byte]
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
        return Location(loc)


    def read_position(self) -> CardPosition:
        pos: int = self.read_int(4)
        return CardPosition(pos)


    def read_phase(self) -> Phase:
        return Phase(self.read_int(4))


    def __repr__(self) -> str:
        return f'<msg_id: {self.msg_id}>' + self._content.hex(' ')


    


