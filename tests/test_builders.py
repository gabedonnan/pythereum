import pytest

import pythereum as pye

from pythereum.exceptions import ERPCRequestException

"""
Each of the following tests sends invalid requests to the given endpoint
Real usage would involve signing a given transaction and passing it into send_private_transaction instead of None

The flashbots builder requires a wallet address and a signed payload to include in the headers for a given transaction
"""


@pytest.mark.asyncio
async def test_titan_builder():
    async with pye.BuilderRPC(pye.TitanBuilder()) as brpc:
        try:
            print(await brpc.send_private_transaction(None))
        except ERPCRequestException as e:
            assert str(e) == "Error -32600: json: cannot unmarshal array into Go value of type ipc.RpcTransaction"


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
            assert str(e) == "Error -32602: invalid argument 0: json: cannot unmarshal non-string into Go value of type hexutil.Bytes"


@pytest.mark.asyncio
async def test_flashbots_builder():
    async with pye.BuilderRPC(pye.FlashbotsBuilder("", "")) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except ERPCRequestException as e:
            assert str(e) == "Error 403: Invalid BuilderRPC request for url https://relay.flashbots.net of form (method=eth_sendPrivateRawTransaction, params=[[{'tx': None, 'preferences': None}]])"