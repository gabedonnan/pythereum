# Example builder submission
import asyncio
from eth_account import Account
from pythereum import BuilderRPC, TitanBuilder, RsyncBuilder, HexStr, NonceManager, Transaction, GasManager, GasStrategy
from dotenv import dotenv_values

erpc_url = dotenv_values("../.env")["TEST_WS"]  # Pulls variables from .env into a dictionary


async def building():
    # Create new arbitrary account wallet
    acct = Account.create()
    # Create an arbitrary transaction
    async with NonceManager(erpc_url) as nm:
        tx = Transaction(
            from_address=acct.address,
            to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
            value=1,
            chain_id=1
        )
        await nm.fill_transaction(tx)

    async with GasManager(erpc_url, 100000) as gm:
        await gm.fill_transaction(tx)

    print(tx)
    # Sign your transaction with your account's key
    signed_tx = Account.sign_transaction(tx, acct.key).rawTransaction

    async with BuilderRPC([TitanBuilder(), RsyncBuilder()], private_key=acct.key) as brpc:
        msg = await brpc.send_private_transaction(HexStr(signed_tx))
        print(msg)


if __name__ == "__main__":
    asyncio.run(building())
