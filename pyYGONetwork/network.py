import asyncio
import asyncio.streams
from typing import Callable, Coroutine, Deque

from pyYGONetwork.packet import Packet


class YGOConnection:
    MAX_PACKET_SIZE : int = 0xffff
    HEADER_SIZE: int = 2

    def __init__(self, hostIP: str, port: int) -> None:
        self.socket: YGOSocket = YGOSocket(hostIP, port)
        self.recieve_callback: Callable[[Packet], None] = None
        self.connect_callback: Callable[[None], None] = None

        # for debug
        self.last_recieved: Packet = None
        self.last_send: Packet = None
        
    @property
    def is_connected(self) -> bool:
        return not self.socket.writer.is_closing()
   

    async def connect(self) -> Coroutine:
        await self.socket.connect()
        self.connect_callback()


    def send(self, packet: Packet) -> None:
        data_tosend: bytes = packet._msg_id + packet.content
        if len(data_tosend) > self.MAX_PACKET_SIZE:
            raise Exception('too large packet')
        
        header: bytes = len(data_tosend).to_bytes(self.HEADER_SIZE, byteorder='little')

        data_tosend = header + data_tosend
        
        self.socket.send(data_tosend)
        self.last_send = packet


    async def listen(self) -> Coroutine:
        while self.is_connected:
            try:
                await self.socket.listen()
            except ConnectionAbortedError:
                self.close()


    async def receive_pending_packet(self) -> bytes:
        while len(self.socket.recieved_data) > 0:
            if self.is_connected:
                await self.socket.writer.drain()
            
            pending: bytes = self.socket.recieved_data.popleft()

            packet: Packet = Packet()
            packet._msg_id = pending[0:1]
            packet.content = pending[1:]
            self.recieve_callback(packet)
            self.last_recieved = packet
            

    def close(self) -> None:
        self.socket.close()


class YGOSocket:
    def __init__(self, hostIP: str, port: int) -> None:
        self.hostIP: str = hostIP
        self.port: int = port
        self.bufsize: int = 0xffff
        self.recieved_data: Deque[bytes] = Deque()

        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None

        self.send_callback: Callable[[None], None] = lambda:None


    async def listen(self) -> Coroutine:
        header: bytes = await self.reader.read(YGOConnection.HEADER_SIZE)
        data_size: int = int.from_bytes(header, byteorder='little')
        if data_size == 0:
            self.close()
        data = await self.reader.read(data_size)
        self.recieved_data.append(data)
            

    async def connect(self) -> Coroutine:
        self.reader, self.writer = await asyncio.streams.open_connection(self.hostIP, self.port)
        

    def send(self, data: bytes) -> None:
        self.writer.write(data)
        

    def close(self) -> None:
        self.writer.close()




if __name__ == '__main__':
    pass
