# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

from asyncio import Queue, gather
from contextlib import asynccontextmanager
from websockets import connect, WebSocketClientProtocol


class WebsocketPool:
    """
    Builds a pool of reusable websockets from which to pull
    Greatly improves speed over having to handshake a new connection for each request
    """

    def __init__(
        self,
        url: str,
        pool_size: int = 6,
        connection_max_payload_size: int = 2**20,
        connection_timeout: int = 20,
    ):
        self._url = url
        self._id = 0
        self._max_pool_size = pool_size
        self._max_payload_size = connection_max_payload_size
        self._timeout = connection_timeout
        self._sockets_used = 0
        self._sockets = Queue(maxsize=pool_size)
        self.connected = False

    async def start(self) -> None:
        """
        Initialises the correct number of connections
        Restarts the websocket pool if run while already connected
        """
        if self.connected:
            await self.quit()
        # Creates a number of sockets equal to the maximum pool size
        sockets = await gather(
            *(
                connect(
                    self._url,
                    max_size=self._max_payload_size,
                    ping_interval=self._timeout,
                )
                for _ in range(self._max_pool_size)
            )
        )
        await gather(*(self._sockets.put(socket) for socket in sockets))
        self._sockets_used = 0
        self.connected = True

    @asynccontextmanager
    async def get_socket(self) -> WebSocketClientProtocol:
        """
        :return: Returns a list of websockets to use
        The websockets will be returned to the main pool upon exiting the with statement in which this should be called
        """
        # Ensures the batch size returned does not exceed the limit
        if not self.connected:
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
        self.connected = False


# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
