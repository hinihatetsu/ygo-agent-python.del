import asyncio
import asyncio.streams

from pyYGONetwork.packet import Packet


class YGOConnection:
    MAX_PACKET_SIZE : int = 0xffff
    HEADER_SIZE: int = 2

    def __init__(self, hostIP: str, port: int) -> None:
        self._hostIP: str = hostIP
        self._port: int = port
        self._recieved_data: asyncio.Queue[bytes] = None

        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamWriter = None

        # for debug
        self.last_recieved: Packet = None
        self.last_send: Packet = None
        
        
    @property
    def is_connected(self) -> bool:
        if self._writer is None:
            return False
        return not self._writer.is_closing()
   

    async def connect(self) -> None:
        self._recieved_data = asyncio.Queue()
        try:
            self._reader, self._writer = await asyncio.streams.open_connection(self._hostIP, self._port)
        except ConnectionRefusedError:
            pass


    def send(self, packet: Packet) -> None:
        data: bytes = packet.data
        size: int = len(data)
        if size > self.MAX_PACKET_SIZE:
            raise Exception('too large packet')
        
        header: bytes = size.to_bytes(self.HEADER_SIZE, byteorder='little')
        self._writer.write(header + data)
        self.last_send = packet


    async def listen(self) -> None:
        while self.is_connected:
            try:
                header: bytes = await self._reader.read(self.HEADER_SIZE)
                data_size: int = int.from_bytes(header, byteorder='little')
                if data_size == 0:
                    self.close()
                    await self._recieved_data.put(b'\x00')
                data = await self._reader.read(data_size)
                await self._recieved_data.put(data)
            except ConnectionAbortedError:
                self.close()


    async def receive_pending_packet(self) -> Packet:
        pending: bytes = await self._recieved_data.get()
        packet: Packet = Packet(int.from_bytes(pending[0:1], 'little'))
        packet.write(pending[1:]) 
        self.last_recieved = packet
        return packet


    async def drain(self) -> None:
        if self.is_connected:
            await self._writer.drain()
            

    def close(self) -> None:
        self._writer.close()



if __name__ == '__main__':
    pass
