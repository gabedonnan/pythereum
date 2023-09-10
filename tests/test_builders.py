import pytest

import pythereum as pye


@pytest.mark.asyncio
async def test_titan_builder():
    async with pye.BuilderRPC(pye.TitanBuilder()) as brpc:
        signed = await brpc.rpc.sign()
        print(await brpc.send_private_transaction(signed))