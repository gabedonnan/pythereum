# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import unittest
import asyncio
from time import time
from pythereum.common import HexStr
from pythereum.rpc import (
    EthRPC,
    SubscriptionType,
    BlockTag,
    convert_eth,
    EthDenomination,
)

# I store the links I use for testing in my .env file under the name "TEST_WS"
from dotenv import dotenv_values

config = dotenv_values(".env")  # Pulls variables from .env into a dictionary

ANVIL_URL = "ws://127.0.0.1:8545"
TEST_URL = config["TEST_WS"]


class MyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.rpc = EthRPC(TEST_URL, 8)
        await self.rpc.start_pool()

    async def asyncTearDown(self) -> None:
        await self.rpc.close_pool()

    async def test_task_group(self):
        rpc = self.rpc

        # It is important to start the websocket pool before task groups
        # This is due to different tasks trying to start the pool simultaneously when run
        t0 = time()
        async with asyncio.TaskGroup() as tg:
            r1 = tg.create_task(rpc.get_block_number())
            r2 = tg.create_task(
                rpc.get_transaction_count("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
            )
            r3 = tg.create_task(
                rpc.get_balance("0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C")
            )
            r4 = tg.create_task(rpc.get_gas_price())
            r5 = tg.create_task(
                rpc.get_block_by_hash(
                    "0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae",
                    False,
                )
            )
            r6 = tg.create_task(rpc.get_block_by_number(17578346, False))
        print(time() - t0)

    async def test_batch_tasks(self):
        await self.rpc.start_pool()
        t0 = time()
        async with asyncio.TaskGroup() as tg:
            t3 = tg.create_task(
                self.rpc.get_block_by_number(
                    [i for i in range(1000, 1010)],
                    full_object=[False for _ in range(10)],
                )
            )

            t4 = tg.create_task(
                self.rpc.get_block_by_number(
                    [i for i in range(3000, 3010)],
                    full_object=[False for _ in range(10)],
                )
            )

            t5 = tg.create_task(
                self.rpc.get_block_by_number(
                    [i for i in range(6000, 6010)],
                    full_object=[False for _ in range(10)],
                )
            )

            t6 = tg.create_task(
                self.rpc.get_block_by_number(
                    [i for i in range(6010, 6020)],
                    full_object=[False for _ in range(10)],
                )
            )

            t7 = tg.create_task(
                self.rpc.get_block_by_number(
                    [i for i in range(6020, 6030)],
                    full_object=[False for _ in range(10)],
                )
            )

            t8 = tg.create_task(
                self.rpc.get_block_by_number(
                    [i for i in range(6030, 6040)],
                    full_object=[False for _ in range(10)],
                )
            )
        print(time() - t0)

    async def test_batch_get_block_by_number(self):
        erpc = self.rpc
        for i in range(20):
            x = (
                asyncio.create_task(
                    erpc.get_block_by_number(
                        [i for i in range(6020, 6030)],
                        full_object=[False for _ in range(10)],
                    )
                )
                for __ in range(120)
            )
            await asyncio.gather(*x)

    async def test_batch_get_balance(self):
        erpc = self.rpc
        for i in range(3):
            x = (
                asyncio.create_task(
                    erpc.get_balance(
                        [
                            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
                            for _ in range(10)
                        ],
                        [BlockTag.latest for __ in range(10)],
                    )
                )
                for __ in range(10)
            )
            await asyncio.gather(*x)

    async def test_batch_get_transaction_count(self):
        erpc = self.rpc
        for i in range(3):
            x = (
                asyncio.create_task(
                    erpc.get_transaction_count(
                        [
                            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
                            for _ in range(10)
                        ],
                        [BlockTag.latest for __ in range(10)],
                    )
                )
                for __ in range(2)
            )
            await asyncio.gather(*x)

    async def test_transaction_count(self):
        r = await self.rpc.get_transaction_count(
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        )
        print(r)
        self.assertIsInstance(r, int)

    async def test_wallet_balance(self):
        print(
            await self.rpc.get_balance(
                [
                    "0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C",
                    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                ],
                [BlockTag.latest, BlockTag.latest],
            )
        )

    async def test_gas_price(self):
        r = await self.rpc.get_gas_price()
        print(convert_eth(r, EthDenomination.wei, EthDenomination.eth))

    async def test_get_block_by_hash(self):
        r = await self.rpc.get_block_by_hash(
            "0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae", False
        )
        print(r)

    async def test_get_block_by_number(self):
        r = await self.rpc.get_block_by_number(BlockTag.latest, True)
        print(r)

    async def test_get_syncing(self):
        r = await self.rpc.get_sync_status()
        print(r)

    async def test_protocol_version(self):
        r = await self.rpc.get_protocol_version()
        print(r)

    async def test_accounts(self):
        r = await self.rpc.get_accounts()
        print(r)

    async def test_batch_transaction_count_by_hash(self):
        r = await self.rpc.get_transaction_count_by_hash(
            [
                HexStr(
                    "0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae"
                ),
                "0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae",
            ]
        )
        print(r)

    async def test_get_transaction_count_by_number(self):
        r = await self.rpc.get_transaction_count_by_number(100000)
        print(r)

    async def test_get_code(self):
        r = await self.rpc.get_code(
            "0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C", 100020
        )
        print(r)

    async def test_unsubscribe(self):
        async with self.rpc.subscribe(SubscriptionType.new_heads) as sc:
            pass

    async def test_create_block_filter(self):
        ftr = await self.rpc.new_block_filter()
        await asyncio.sleep(
            10
        )  # Waits an amount of time for new blocks to hopefully be created
        r = await self.rpc.get_filter_changes(ftr)
        print(r)

    async def test_create_filter(self):
        ftr = await self.rpc.new_filter(
            from_block=30_000,
            to_block=30_010,
            address=[
                "0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C",
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            ],
            topics=[
                "0x2c76e7a47fd53e2854856ac3f0a5f3ee40d15cfaa82266357ea9779c486ab9c3"
            ],
        )
        r = await self.rpc.get_filter_changes(ftr)
        print(r)

    async def test_net_functions(self):
        msg = await self.rpc.get_net_version()
        print(msg)
        msg = await self.rpc.get_net_listening()
        print(msg)
        msg = await self.rpc.get_net_peer_count()
        print(msg)

    async def test_experimental(self):
        # msg = await self.rpc.get_fee_history(
        #     [4, 5, 6],
        #     ["latest", "latest", "latest"],
        #     [[25, 75], [25, 75], [25, 75]]
        # )
        # print(msg)
        msg = await self.rpc.get_proof(
            "0x7F0d15C7FAae65896648C8273B6d7E43f58Fa842",
            ["0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"],
            "latest",
        )
        print(msg)

    async def test_w3_functions(self):
        msg = await self.rpc.get_client_version()
        print(msg)
        msg = await self.rpc.sha3("0x68656c6c6f20776f726c64")
        print(msg)

    async def test_with(self):
        async with EthRPC(ANVIL_URL, 1) as rpc:
            await rpc.get_net_version()

    async def test_aio(self):
        async with EthRPC(TEST_URL, use_socket_pool=False) as erpc:
            async with asyncio.TaskGroup() as tg:
                for i in range(40):
                    tg.create_task(erpc.get_block_by_number(i, True))
                    tg.create_task(erpc.get_block_number())

        async with EthRPC(url=ANVIL_URL, use_socket_pool=False) as rpc:
            print(await rpc.get_net_version())

    async def test_mempool_geth(self):
        async with EthRPC(
            "https://docs-demo.quiknode.pro/", use_socket_pool=False
        ) as erpc:
            print((await erpc.get_mempool_geth()).pending)


if __name__ == "__main__":
    unittest.main()

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
