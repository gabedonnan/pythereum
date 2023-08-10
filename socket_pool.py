import asyncio
import websockets
from contextlib import asynccontextmanager


class WebsocketPool:
    """
    Builds a pool of reusable websockets from which to pull
    Greatly improves speed over having to handshake a new connection for each request
    """
    def __init__(self, url: str, pool_size: int = 20):
        self._url = url
        self._id = 0
        self._max_pool_size = pool_size
        self._sockets_used = 0
        self._sockets = asyncio.Queue(maxsize=pool_size)
        self._connected = False

    async def start(self) -> None:
        """
        Initialises the correct number of connections
        Restarts the websocket pool if run while already connected
        """
        if self._connected:
            await self.quit()
        # Creates a number of sockets equal to the maximum pool size
        # connections = await asyncio.gather(websockets.connect(self._url) for _ in range(self._max_pool_size))
        for _ in range(self._max_pool_size):
            await self._sockets.put(await websockets.connect(self._url, ping_interval=5))
        self._sockets_used = 0
        self._connected = True

    @asynccontextmanager
    async def get_socket(self) -> websockets.WebSocketClientProtocol:
        """
        :return: Returns a list of websockets to use
        The websockets will be returned to the main pool upon exiting the with statement in which this should be called
        """
        # Ensures the batch size returned does not exceed the limit
        if not self._connected:
            # Ensures that get_socket can be called without needing to explicitly call start() beforehand
            await self.start()
        socket = await self._sockets.get()
        try:
            self._sockets_used += 1
            yield socket
        finally:
            self._sockets.task_done()
            self._sockets.put_nowait(socket)
            self._sockets_used -= 1

    async def quit(self) -> None:
        """
        Pulls all sockets from the object queue, closes them and resets variables
        """
        while not self._sockets.empty():
            sock = self._sockets.get_nowait()
            await sock.close()
            self._sockets.task_done()
        self._sockets_used = 0
        self._connected = False
