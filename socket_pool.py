import asyncio
import websockets


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

    async def start(self):
        """
        Initialises the correct number of connections
        Restarts the websocket pool if run while already connected
        """
        if self._connected:
            await self.quit()
            self._connected = False
        # Creates a number of sockets equal to the maximum pool size
        connections = await asyncio.gather(websockets.connect(self._url) for _ in range(self._max_pool_size))
        for connection in connections:
            await self._sockets.put(connection)
        self._sockets_used = 0
        self._connected = True

    async def get_sockets(self, batch_size: int = 1) -> list[websockets.legacy.client.WebSocketClientProtocol]:
        # Ensures the batch size returned does not exceed the limit
        batch_size = min(self._max_pool_size - self._sockets_used, batch_size)
        if not self._connected:
            # Ensures that get_socket can be called without needing to explicitly call start() beforehand
            await self.start()
        sockets = [self._sockets.get_nowait() for _ in range(batch_size)]
        self._sockets_used += 1
        try:
            yield sockets
        finally:
            for socket in sockets:
                self._sockets.put_nowait(socket)
            self._sockets_used -= 1

    async def quit(self):
        ...
