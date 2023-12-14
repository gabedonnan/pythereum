import pytest

import pythereum as pye

from eth_account import Account
from pythereum.exceptions import ERPCRequestException

"""
Each of the following tests sends invalid requests to the given endpoint
Real usage would involve signing a given transaction and passing it into send_private_transaction instead of None

The flashbots builder requires a wallet address and a signed payload to include in the headers for a given transaction

More comprehensive tests will be generated for these at a later date
"""


@pytest.mark.asyncio
async def test_titan_builder():
    async with pye.BuilderRPC(pye.TitanBuilder(), Account.create().key) as brpc:
        try:
            print(await brpc.send_private_transaction(None))
        except ERPCRequestException as e:
            assert (
                str(e)
                == "Error -32600: json: cannot unmarshal array into Go value of type ipc.RpcTransaction"
                   "\nPlease consult your endpoint's documentation for info on error codes."
            )


@pytest.mark.asyncio
async def test_rsync_builder():
    async with pye.BuilderRPC(pye.RsyncBuilder()) as brpc:
        assert await brpc.send_private_transaction(None) is None


@pytest.mark.asyncio
async def test_0x69_builder():
    async with pye.BuilderRPC(pye.Builder0x69()) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except ERPCRequestException as e:
            assert str(e) == (
                "Error -32602: invalid argument 0: json: cannot unmarshal non-string into Go value of "
                "type hexutil.Bytes\nPlease consult your endpoint's documentation for info on error codes."
            )


@pytest.mark.asyncio
async def test_flashbots_builder():
    async with pye.BuilderRPC(pye.FlashbotsBuilder(), Account.create().key) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except ERPCRequestException as e:
            assert str(e) == (
                "Error 403: Invalid BuilderRPC request for url https://relay.flashbots.net of form ("
                "method=eth_sendPrivateRawTransaction, params=[{'tx': None, 'preferences': None}])"
                "\nPlease consult your endpoint's documentation for info on error codes."
            )


@pytest.mark.asyncio
async def test_loki_builder():
    async with pye.BuilderRPC(pye.LokiBuilder()) as brpc:
        assert await brpc.send_private_transaction(None) is None


@pytest.mark.asyncio
async def test_all_builders():
    async with pye.BuilderRPC(
        pye.ALL_BUILDERS, private_key=Account.create().key
    ) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except ERPCRequestException as e:
            assert str(e) == ("Error -32000: no transaction found"
                              "\nPlease consult your endpoint's documentation for info on error codes.")
