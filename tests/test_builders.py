# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import pytest
import logging
import sys

import pythereum as pye

from eth_account import Account
from pythereum.exceptions import PythereumRequestException

"""
Each of the following tests sends invalid requests to the given endpoint
Real usage would involve signing a given transaction and passing it into send_private_transaction instead of None

The flashbots builder requires a wallet address and a signed payload to include in the headers for a given transaction

More comprehensive tests will be generated for these at a later date
"""

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


@pytest.mark.asyncio
async def test_titan_builder():
    async with pye.BuilderRPC(pye.TitanBuilder(), Account.create().key) as brpc:
        try:
            print(await brpc.send_private_transaction(None))
        except PythereumRequestException as e:
            assert (
                str(e)
                == "Error -32000: no transaction found for builder https://rpc.titanbuilder.xyz"
                "\nPlease consult your endpoint's documentation for info on error codes."
            )


@pytest.mark.asyncio
async def test_rsync_builder():
    async with pye.BuilderRPC(pye.RsyncBuilder()) as brpc:
        assert await brpc.send_private_transaction(None) == [None]


@pytest.mark.asyncio
async def test_0x69_builder():
    async with pye.BuilderRPC(pye.Builder0x69()) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except PythereumRequestException as e:
            assert str(e) == (
                "Error -32602: invalid argument 0: json: cannot unmarshal non-string into Go value of "
                "type hexutil.Bytes for builder https://builder0x69.io/"
                "\nPlease consult your endpoint's documentation for info on error codes."
            )


@pytest.mark.asyncio
async def test_flashbots_builder():
    async with pye.BuilderRPC(pye.FlashbotsBuilder(), Account.create().key) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except PythereumRequestException as e:
            assert str(e) == (
                "Error 403: Invalid BuilderRPC request for url https://relay.flashbots.net of form ("
                "method=eth_sendPrivateRawTransaction, params=[{'tx': None, 'preferences': None}])"
                "\nPlease consult your endpoint's documentation for info on error codes."
            )


@pytest.mark.asyncio
async def test_all_builders():
    async with pye.BuilderRPC(
        pye.ALL_BUILDERS, private_key=Account.create().key
    ) as brpc:
        try:
            await brpc.send_private_transaction(None)
        except PythereumRequestException as e:
            assert str(e) in (
                "Error 400: Invalid BuilderRPC request "
                "for url https://rpc.beaverbuild.org/ of form (method=eth_sendPrivateRawTransaction, params=[None])"
                "\nPlease consult your endpoint's documentation for info on error codes.",
                "Error -32000: no transaction found for builder https://rpc.titanbuilder.xyz"
                "\nPlease consult your endpoint's documentation for info on error codes.",
                "Error -32602: invalid argument 0: json: cannot unmarshal non-string into "
                "Go value of type hexutil.Bytes for builder https://builder0x69.io/"
                "\nPlease consult your endpoint's documentation for info on error codes.",
            )


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
