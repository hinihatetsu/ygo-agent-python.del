import asyncio
import asyncio.streams
from typing import Deque

from pyYGONetwork.packet import Packet


class YGOConnection:
    MAX_PACKET_SIZE : int = 0xffff
    HEADER_SIZE: int = 2

    def __init__(self, hostIP: str, port: int) -> None:
        self.hostIP: str = hostIP
        self.port: int = port
        self.recieved_data: Deque[bytes] = Deque()

        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None

        # for debug
        self.last_recieved: Packet = None
        self.last_send: Packet = None
        
        
    @property
    def is_connected(self) -> bool:
        return not self.writer.is_closing()
   

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.streams.open_connection(self.hostIP, self.port)


    def send(self, packet: Packet) -> None:
        data: bytes = packet._msg_id + packet.content
        if len(data) > self.MAX_PACKET_SIZE:
            raise Exception('too large packet')
        
        header: bytes = len(data).to_bytes(self.HEADER_SIZE, byteorder='little')

        data = header + data
        
        self.writer.write(data)
        self.last_send = packet


    async def listen(self) -> None:
        while self.is_connected:
            try:
                header: bytes = await self.reader.read(self.HEADER_SIZE)
                data_size: int = int.from_bytes(header, byteorder='little')
                if data_size == 0:
                    self.close()
                data = await self.reader.read(data_size)
                self.recieved_data.append(data)
            except ConnectionAbortedError:
                self.close()


    async def receive_pending_packet(self) -> Packet:
        while True:
            try:
                pending: bytes = self.recieved_data.popleft()
                break
            except IndexError:
                await asyncio.sleep(0.1) 

        packet: Packet = Packet()
        packet._msg_id = pending[0:1]
        packet.content = pending[1:]
        self.last_recieved = packet
        return packet


    async def drain(self) -> None:
        if self.is_connected:
            await self.writer.drain()
            

    def close(self) -> None:
        self.writer.close()


class YGOSocket:
    def __init__(self, hostIP: str, port: int) -> None:
        self.hostIP: str = hostIP
        self.port: int = port
        self.bufsize: int = 0xffff
        self.recieved_data: Deque[bytes] = Deque()

        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None



    async def listen(self) -> None:
        header: bytes = await self.reader.read(YGOConnection.HEADER_SIZE)
        data_size: int = int.from_bytes(header, byteorder='little')
        if data_size == 0:
            self.close()
        data = await self.reader.read(data_size)
        self.recieved_data.append(data)
            

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.streams.open_connection(self.hostIP, self.port)
        

    def send(self, data: bytes) -> None:
        self.writer.write(data)
        

    def close(self) -> None:
        self.writer.close()



if __name__ == '__main__':
    pass
