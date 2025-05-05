# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

# Example demonstration of builder submission, alongside implementations of gas and nonce managers
import asyncio
import logging
import sys

from eth_account import Account
from pythereum import (
    BuilderRPC,
    TitanBuilder,
    RsyncBuilder,
    HexStr,
    NonceManager,
    Transaction,
    GasManager,
    EthRPC,
)
from dotenv import dotenv_values

erpc_url = dotenv_values("../.env")[
    "TEST_WS"
]  # Pulls variables from .env into a dictionary

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

    signed_tx = Account.sign_transaction(tx, acct.key).raw_transaction

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
