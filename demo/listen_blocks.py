import asyncio

from main import EthRPC, SubscriptionTypes
from dotenv import dotenv_values
config = dotenv_values("../.env")  # Pulls variables from .env into a dictionary

async def listen_blocks(url):
    erpc = EthRPC(url, 4)
    await erpc.start_pool()
    async with erpc.subscribe(SubscriptionTypes.new_heads) as sc:
        async for header in sc.recv():
            # print(header.hash.hex_string)
            block = await erpc.get_block_by_hash(header.hash.hex_string, False)
            for tx in block.transactions:
                r = await erpc.get_transaction_receipt(tx.hex_string)
                print(r)

if __name__ == '__main__':
    asyncio.run(listen_blocks(config["TEST_WS"]))