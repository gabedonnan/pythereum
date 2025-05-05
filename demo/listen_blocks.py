# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import asyncio
import logging
import sys
from time import time

from pythereum import EthRPC, SubscriptionType
from dotenv import dotenv_values

config = dotenv_values("../.env")  # Pulls variables from .env into a dictionary

handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(name)s] : %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

root = logging.getLogger()
root.handlers = []
root.addHandler(handler)
root.setLevel(logging.DEBUG)

logging.getLogger("websockets").setLevel(logging.WARNING)


async def listen_blocks(url):
    """
    Function to create a new_heads subscription, use the hash from each header received to get full block info.
    That full block info is then used to get all transaction receipts from that given block.
    """
    prev = 0
    # Create EthRPC object with pool size of 2 (arbitrarily chosen, as it does not matter here)
    erpc = EthRPC(url, 2, connection_max_payload_size=2**24)

    # Start the socket pool, may take a while due to connection forming
    await erpc.start_pool()

    # Create + context manage new_heads subscription
    async with erpc.subscribe(SubscriptionType.new_heads, 80) as sc:
        # Loops forever over the received data from the subscription
        async for header in sc.recv():
            # Gets more block data from the hash received from the headers
            print((t0 := time()) - prev)
            prev = t0
            # block = await erpc.get_block_by_hash(header.hash, True)
            # # Iterates through the transactions found in retrieved data
            # for tx in block.transactions:
            # print(tx)

    await erpc.close_pool()


if __name__ == "__main__":
    asyncio.run(listen_blocks(config["TEST_WS"]))

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
