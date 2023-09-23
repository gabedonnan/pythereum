# Example builder submission
import asyncio
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
    manager_rpc = EthRPC(erpc_url, 1)

    # Fill the nonce value of the transaction automatically
    async with NonceManager(manager_rpc) as nm:
        await nm.fill_transaction(tx)

    # Define gas strategies for each facet of the GasManager
    gas_strategy = {
        "gas": GasStrategy.lower_quartile_price,
        "maxFeePerGas": GasStrategy.mean_price,
        "maxPriorityFeePerGas": GasStrategy.min_price
    }
    # Fill the transactions gas, priority fee, and fee prices in the transaction
    async with GasManager(
            manager_rpc,
            max_gas_price=EthDenomination.picoether,
            max_priority_price=3 * EthDenomination.microether,
            max_fee_price=3 * EthDenomination.microether
    ) as gm:
        await gm.fill_transaction(tx, strategy=gas_strategy)

    # Sign your transaction with your account's key
    signed_tx = Account.sign_transaction(tx, acct.key).rawTransaction

    async with BuilderRPC([TitanBuilder(), RsyncBuilder()], private_key=acct.key) as brpc:
        msg = await brpc.send_private_transaction(HexStr(signed_tx))
        print(msg)


if __name__ == "__main__":
    asyncio.run(building())
