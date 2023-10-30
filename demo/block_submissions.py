# Example demonstration of builder submission, alongside implementations of gas and nonce managers
import asyncio
from time import time
from eth_account import Account
from pythereum import (
    BuilderRPC,
    TitanBuilder,
    RsyncBuilder,
    HexStr,
    NonceManager,
    Transaction,
    GasManager,
    GasStrategy,
    EthRPC,
    EthDenomination,
)
from dotenv import dotenv_values

erpc_url = dotenv_values("../.env")[
    "TEST_WS"
]  # Pulls variables from .env into a dictionary


async def building():
    # Create new arbitrary account wallet
    acct = Account.create()
    # Create an arbitrary transaction (minus gas and nonce values)
    tx = Transaction(
        from_address=acct.address,
        to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
        value=1,
        chain_id=1,
    )
    manager_rpc = EthRPC(erpc_url, 2)

    # Works differently to NonceManager, in that it manages multiple strategies
    gm = GasManager(manager_rpc)

    await manager_rpc.start_pool()

    async with NonceManager(manager_rpc) as nm:
        await nm.fill_transaction(tx)

    async with gm.informed_manager() as im:
        im.fill_transaction(tx)

    print(tx)

    signed_tx = Account.sign_transaction(tx, acct.key).rawTransaction

    async with BuilderRPC(
        [TitanBuilder(), RsyncBuilder()], private_key=acct.key
    ) as brpc:
        msg = await brpc.send_private_transaction(HexStr(signed_tx))
        print(msg)

    # Let us imagine our transaction has failed, due to an execution reversion, meaning we need to up our priority fee
    # This can be verified by checking transaction receipts for success / failure states
    transaction_failed = True

    if transaction_failed:
        # The GasManager class saves information from previous usages of informed_manager() for speed
        # This can be bypassed with gm.clear_informed_info()
        async with gm.informed_manager() as im:
            im.execution_fail()
            im.fill_transaction(tx)

    print(tx)

    # As we can see the transaction's priority fee went up! But what if we succeed in this next transaction?
    # We would like to lower the price we pay ever so slightly, to pay as little as possible.

    # Imagined submission

    transaction_failed = False

    if not transaction_failed:
        async with gm.informed_manager() as im:
            im.execution_success()
            im.fill_transaction(tx)

    print(tx)

    # As we can see, its priority fee has gone down!

    # Using async with gm.informed_manager() as im so many times may seem inefficient
    # Indeed it is not necessary, but it does not actually slow the program down at all due to GasManager storing info

    # If we would like to instead naively base our prices on previous block prices we can use a naive gas manager

    async with gm.naive_manager() as nm:
        await nm.fill_transaction(tx)

    print(tx)

    await manager_rpc.close_pool()


if __name__ == "__main__":
    asyncio.run(building())
