import unittest
import asyncio
from time import time
from eth_rpc.rpc import EthRPC, SubscriptionType, BlockTag
# I store the links I use for testing in my .env file under the name "TEST_WS"
from dotenv import dotenv_values

config = dotenv_values(".env")  # Pulls variables from .env into a dictionary

ANVIL_URL = "ws://127.0.0.1:8545"


class MyTestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.erpc_ws = EthRPC(config["TEST_WS"], 20)
        await self.erpc_ws.start_pool()

    async def asyncTearDown(self) -> None:
        await self.erpc_ws.close_pool()

    async def test_block_num(self):
        erpc_ws = self.erpc_ws
        await erpc_ws.start_pool()
        t0 = time()
        async with asyncio.TaskGroup() as tg:
            r1 = tg.create_task(erpc_ws.get_block_number())
            r2 = tg.create_task(erpc_ws.get_transaction_count("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"))
            r3 = tg.create_task(erpc_ws.get_balance("0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C"))
            r4 = tg.create_task(erpc_ws.get_gas_price())
            r5 = tg.create_task(
                erpc_ws.get_block_by_hash("0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae", False))
            r6 = tg.create_task(erpc_ws.get_block_by_number(17578346, False))
        print(time() - t0)

    async def test_batch_tasks(self):
        await self.erpc_ws.start_pool()
        t0 = time()
        async with asyncio.TaskGroup() as tg:
            t3 = tg.create_task(self.erpc_ws.get_block_by_number(
                [i for i in range(1000, 1010)],
                full_object=[False for _ in range(10)]
            ))

            t4 = tg.create_task(self.erpc_ws.get_block_by_number(
                [i for i in range(3000, 3010)],
                full_object=[False for _ in range(10)]
            ))

            t5 = tg.create_task(self.erpc_ws.get_block_by_number(
                [i for i in range(6000, 6010)],
                full_object=[False for _ in range(10)]
            ))

            t6 = tg.create_task(self.erpc_ws.get_block_by_number(
                [i for i in range(6010, 6020)],
                full_object=[False for _ in range(10)]
            ))

            t7 = tg.create_task(self.erpc_ws.get_block_by_number(
                [i for i in range(6020, 6030)],
                full_object=[False for _ in range(10)]
            ))

            t8 = tg.create_task(self.erpc_ws.get_block_by_number(
                [i for i in range(6030, 6040)],
                full_object=[False for _ in range(10)]
            ))
        print(time() - t0)

    async def test_batch_get_block_by_number(self):
        erpc = self.erpc_ws
        for i in range(20):
            x = (asyncio.create_task(erpc.get_block_by_number(
                [i for i in range(6020, 6030)],
                full_object=[False for _ in range(10)]
            )) for __ in range(120))
            await asyncio.gather(*x)

    async def test_batch_get_balance(self):
        erpc = self.erpc_ws
        for i in range(3):
            x = (asyncio.create_task(erpc.get_balance(
                ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" for _ in range(10)],
                [BlockTag.latest for __ in range(10)]
            )) for __ in range(10))
            await asyncio.gather(*x)

    async def test_batch_get_transaction_count(self):
        erpc = self.erpc_ws
        for i in range(3):
            x = (asyncio.create_task(erpc.get_transaction_count(
                ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" for _ in range(10)],
                [BlockTag.latest for __ in range(10)]
            )) for __ in range(2))
            await asyncio.gather(*x)

    async def test_transaction_count(self):
        r = await self.erpc_ws.get_transaction_count("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
        self.assertIsInstance(r, int)

    async def test_wallet_balance(self):
        print(await self.erpc_ws.get_balance(
            ["0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C", "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
            [BlockTag.latest, BlockTag.latest]))

    async def test_gas_price(self):
        self.assertIsInstance(await self.erpc_ws.get_gas_price(), int)

    async def test_get_block_by_hash(self):
        r = await self.erpc_ws.get_block_by_hash("0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae",
                                                 False)
        print(r)

    async def test_get_block_by_number(self):
        r = await self.erpc_ws.get_block_by_number(17578346, False)
        print(r)


if __name__ == '__main__':
    unittest.main()
