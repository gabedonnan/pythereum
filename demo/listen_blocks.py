import asyncio

from eth_rpc.rpc import EthRPC, SubscriptionType
from dotenv import dotenv_values

config = dotenv_values("../.env")  # Pulls variables from .env into a dictionary


async def listen_blocks(url):
    # Create EthRPC object with pool size of 2 (arbitrarily chosen, as it does not matter here)
    erpc = EthRPC(url, 2)

    # Start the socket pool, may take a while due to connection forming
    await erpc.start_pool()

    # Create + context manage new_heads subscription
    async with erpc.subscribe(SubscriptionType.new_heads) as sc:
        # Loops forever over the received data from the subscription
        async for header in sc.recv():
            # Gets more block data from the hash received from the headers
            block = await erpc.get_block_by_hash(header.hash, True)

            # Iterates through the transactions found in retrieved data
            for tx in block.transactions:
                # Gets and prints the receipts for each transaction
                r = await erpc.get_transaction_receipt(tx.hash)
                print(r)
    await erpc.close_pool()


if __name__ == '__main__':
    asyncio.run(listen_blocks(config["TEST_WS"]))
