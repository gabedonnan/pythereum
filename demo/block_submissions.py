# Example builder submission
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
    EthDenomination
)
from dotenv import dotenv_values

erpc_url = dotenv_values("../.env")["TEST_WS"]  # Pulls variables from .env into a dictionary


async def building():
    # Create new arbitrary account wallet
    acct = Account.create()
    # Create an arbitrary transaction (minus gas and nonce values)
    tx = Transaction(
        from_address=acct.address,
        to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
        value=1,
        chain_id=1
    )
    # Define gas strategies for each facet of the GasManager
    gas_strategy = {
        "gas": GasStrategy.mode_price,
        "maxFeePerGas": GasStrategy.mean_price,
        "maxPriorityFeePerGas": GasStrategy.mean_price
    }
    manager_rpc = EthRPC(erpc_url, 1)

    # With statements allow for easy management of RPC websocket opening and closing, standard code is faster

    # With statement example

    t0 = time()
    # Fill the nonce value of the transaction automatically
    async with NonceManager(manager_rpc) as nm:
        await nm.fill_transaction(tx)

    # Fill the transactions gas, priority fee, and fee prices in the transaction
    async with GasManager(
            manager_rpc,
            max_gas_price=EthDenomination.picoether,
            max_priority_price=3 * EthDenomination.microether,
            max_fee_price=3 * EthDenomination.microether
    ) as gm:
        await gm.fill_transaction(tx, strategy=gas_strategy)
    print(f"{tx} formed in {time() - t0} seconds taken with with statements (context managed)")
    # Standard code example

    t0 = time()
    await manager_rpc.start_pool()
    nm = NonceManager(manager_rpc)
    gm = GasManager(
            manager_rpc,
            max_gas_price=EthDenomination.picoether,
            max_priority_price=3 * EthDenomination.microether,
            max_fee_price=3 * EthDenomination.microether
    )
    await nm.fill_transaction(tx)
    await gm.fill_transaction(tx, strategy=gas_strategy)
    await manager_rpc.close_pool()
    print(f"{tx} formed in {time() - t0} seconds taken without with statements (not context managed)")

    # Using AIOHTTP without a websocket pool
    # This is fastest in this case because only 2 RPCs need to be made
    # The websocket pool is more optimal for when many procedure calls are made,
    # as it allows them to be executed in parallel

    t0 = time()
    socketless_manager_rpc = EthRPC(erpc_url, use_socket_pool=False)
    async with NonceManager(socketless_manager_rpc) as nm:
        await nm.fill_transaction(tx)

    async with GasManager(
            socketless_manager_rpc,
            max_gas_price=EthDenomination.picoether,
            max_priority_price=3 * EthDenomination.microether,
            max_fee_price=3 * EthDenomination.microether
    ) as gm:
        await gm.fill_transaction(tx, strategy=gas_strategy)
    print(f"{tx} formed in {time() - t0} seconds taken with aiohttp")

    # Sign your transaction with your account's key
    signed_tx = Account.sign_transaction(tx, acct.key).rawTransaction

    async with BuilderRPC([TitanBuilder(), RsyncBuilder()], private_key=acct.key) as brpc:
        msg = await brpc.send_private_transaction(HexStr(signed_tx))
        print(msg)


if __name__ == "__main__":
    asyncio.run(building())
