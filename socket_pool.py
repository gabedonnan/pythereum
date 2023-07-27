import asyncio
import websockets


class WebsocketPool:
    def __init__(self, url: str, pool_size: int = 20):
        self._url = url
        self._id = 0
        self._max_pool_size = pool_size
        self._current_size = 0
        self.sockets = asyncio.Queue()
        self.connected = False

    async def start(self):
        if self.connected:
            await self.quit()
            self.connected = False
        # Creates a number of sockets equal to the maximum pool size
        connections = await asyncio.gather(self.open_socket() for _ in range(self._max_pool_size))
        for connection in connections:
            self.sockets.put_nowait(connection)

    async def open_socket(self):
        try:
            yield websockets.connect(self._url)
        finally:
            ...

    async def quit(self):
        ...
