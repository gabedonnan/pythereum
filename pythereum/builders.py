# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file
from abc import ABC
from typing import Any

import asyncio
import json
import aiohttp

from eth_account import Account, messages
from eth_utils import keccak

from pythereum.common import HexStr
from pythereum.dclasses import Bundle, MEVBundle
from pythereum.exceptions import PythereumBuilderException, PythereumRequestException
from pythereum.rpc import parse_results


class Builder(ABC):
    def __init__(
        self,
        url: str,
        private_transaction_method: str = "eth_sendPrivateTransaction",
        bundle_method: str = "eth_sendBundle",
        cancel_bundle_method: str = "eth_cancelBundle",
        builder_name: str = "Builder",
        bundle_params: set = None,
    ):
        if bundle_params is None:
            bundle_params = {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
                "refundTxHashes",
            }

        self.url = url
        self.private_transaction_method = private_transaction_method
        self.bundle_method = bundle_method
        self.cancel_bundle_method = cancel_bundle_method
        self.builder_name = builder_name
        self.bundle_params = bundle_params
        super().__init__()

    def format_private_transaction(
        self,
        tx: str | HexStr | list[str] | list[HexStr],
        max_block_number: str | HexStr | list[str] | list[HexStr] | None = None,
    ) -> list[Any]:
        return [[tx, max_block_number]]

    def format_bundle(self, bundle: dict | Bundle) -> list[dict]:
        return [{key: bundle[key] for key in bundle.keys() & self.bundle_params}]

    def format_cancellation(self, uuids: HexStr | str | list[HexStr] | list[str]):
        return [uuids]

    def __hash__(self):
        return self.builder_name


class TitanBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://rpc.titanbuilder.xyz",
            "eth_sendPrivateTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "Titan",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundIndex",
                "refundRecipient",
            },
        )

    def format_private_transaction(
        self,
        tx: str | HexStr | list[str] | list[HexStr],
        max_block_number: str | HexStr | list[str] | list[HexStr] | None = None,
    ) -> list[dict]:
        res = {"tx": tx}
        if max_block_number is not None:
            res["maxBlockNumber"] = max_block_number
        return [res]


class BeaverBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://rpc.beaverbuild.org/",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_sendBundle",
            "beaverbuild.org",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "uuid",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
            },
        )

    def format_private_transaction(
        self,
        tx: str | HexStr | list[str] | list[HexStr],
        max_block_number: str | HexStr | list[str] | list[HexStr] | None = None,
    ) -> list[Any]:
        return [tx]

    def format_cancellation(self, uuids: HexStr | str | list[HexStr] | list[str]):
        if isinstance(uuids, str):
            return [Bundle(uuid=uuids, txs=[])]
        return [[Bundle(uuid=uuid, txs=[]) for uuid in uuids]]


class RsyncBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://rsync-builder.xyz/",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "rsync",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
                "refundTxHashes",
            },
        )

    def format_private_transaction(
        self,
        tx: str | HexStr | list[str] | list[HexStr],
        max_block_number: str | HexStr | list[str] | list[HexStr] | None = None,
    ) -> list[Any]:
        return [tx]


class Builder0x69(Builder):
    def __init__(self):
        super().__init__(
            "https://builder0x69.io/",
            "eth_sendRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "builder0x69",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "uuid",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
            },
        )

    def format_private_transaction(
        self,
        tx: str | HexStr | list[str] | list[HexStr],
        max_block_number: str | HexStr | list[str] | list[HexStr] | None = None,
    ) -> list[Any]:
        return [tx]


class FlashbotsBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://relay.flashbots.net",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "flashbots",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestep",
                "revertingTxHashes",
                "replacementUuid",
            },
        )

    def format_private_transaction(
        self, tx: str | HexStr | list[str] | list[HexStr], preferences: dict = None
    ) -> list[Any]:
        return [{"tx": tx, "preferences": preferences}]


class LokiBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://rpc.lokibuilder.xyz/",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "Loki",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
                "refundTxHashes",
            },
        )

    def format_private_transaction(
        self,
        tx: str | HexStr | list[str] | list[HexStr],
        max_block_number: str | HexStr | list[str] | list[HexStr] | None = None,
    ) -> list[Any]:
        return [tx]


# Tuple of the types of builders which use flashbots headers for their transactions
FLASHBOTS_BUILDER_TYPES = (
    FlashbotsBuilder,
    TitanBuilder,
)

# A list containing all the current supported builders. Can be passed in to a BuilderRPC to send to all
ALL_BUILDERS = (
    TitanBuilder(),
    Builder0x69(),
    RsyncBuilder(),
    BeaverBuilder(),
    FlashbotsBuilder(),
    LokiBuilder(),
)


class BuilderRPC:
    """
    An RPC class designed for sending raw transactions and bundles to specific block builders
    """

    def __init__(
        self,
        builders: Builder | list[Builder],
        private_key: str
        | bytes
        | HexStr
        | list[str]
        | list[bytes]
        | list[HexStr] = None,
    ):
        if isinstance(builders, Builder):
            builders = [builders]

        self.builders = builders

        if isinstance(private_key, HexStr):
            private_key = private_key.hex_bytes
        elif isinstance(private_key, str):
            private_key = HexStr(private_key).hex_bytes

        self.private_key: bytes = private_key
        self.session = None
        self._id = 0

    async def __aenter__(self):
        await self.start_session()
        return self

    async def __aexit__(self, *args):
        await self.close_session()

    def _next_id(self) -> None:
        self._id += 1

    def _get_flashbots_header(self, payload: str = "") -> dict:
        payload = messages.encode_defunct(keccak(text=payload))
        return {
            "X-Flashbots-Signature": f"{Account.from_key(self.private_key).address}:"
            f"{Account.sign_message(payload, self.private_key).signature.hex()}"
        }

    def _build_json(
        self, method: str, params: list[Any], increment: bool = True
    ) -> dict:
        """
        :param method: ethereum RPC method
        :param params: list of parameters to use in the function call, cast to string so Hex data may be used
        :param increment: Boolean determining whether self._id will be advanced after the json is built
        :return: json dictionary
        """
        res = {"jsonrpc": "2.0", "method": method, "params": params, "id": self._id}

        if increment:
            self._next_id()
        return res

    async def _send_message(
        self,
        builder: Builder,
        method: str | list[str],
        params: list[Any],
        use_flashbots_signature: bool = False,
    ):
        if self.session is not None:
            constructed_json = self._build_json(method, params)
            header_data = (
                self._get_flashbots_header(json.dumps(constructed_json))
                if use_flashbots_signature and self.private_key is not None
                else None
            )
            async with self.session.post(
                builder.url, json=constructed_json, headers=header_data
            ) as resp:
                if resp.status != 200:
                    raise PythereumRequestException(
                        resp.status,
                        f"Invalid BuilderRPC request for url {builder.url} of form "
                        f"(method={method}, params={params})",
                    )

                msg = await resp.json()
        else:
            raise PythereumBuilderException(
                "BuilderRPC session not started. Either context manage this class or call BuilderRPC.start_session()"
            )

        return parse_results(msg, builder=builder.url)

    async def start_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def send_private_transaction(
        self,
        tx: str | HexStr,
        extra_info: Any = None,
    ) -> Any:
        return await asyncio.gather(
            *(
                self._send_message(
                    builder,
                    builder.private_transaction_method,
                    builder.format_private_transaction(tx, extra_info),
                    isinstance(builder, FLASHBOTS_BUILDER_TYPES),
                )
                for builder in self.builders
            )
        )

    async def send_bundle(
        self,
        bundle: Bundle,
    ) -> Any:
        return await asyncio.gather(
            *(
                self._send_message(
                    builder,
                    builder.bundle_method,
                    builder.format_bundle(bundle),
                    isinstance(builder, FLASHBOTS_BUILDER_TYPES),
                )
                for builder in self.builders
            )
        )

    async def cancel_bundle(
        self,
        replacement_uuid: str | HexStr,
    ):
        return await asyncio.gather(
            *(
                self._send_message(
                    builder,
                    builder.cancel_bundle_method,
                    builder.format_cancellation(replacement_uuid),
                    isinstance(builder, FLASHBOTS_BUILDER_TYPES),
                )
                for builder in self.builders
            )
        )

    async def send_mev_bundle(self, bundle: MEVBundle) -> Any:
        """
        Sends a MEV bundle to the flashbots builder
        Attempts to distribute the bundle among all builders in the BuilderRPC
        May not work with builders not currently supporting the MEV protocol
        """
        if "privacy" in bundle:
            bundle["privacy"]["builders"].extend(
                [builder.builder_name for builder in self.builders]
            )
        else:
            bundle["privacy"] = {
                "builders": [builder.builder_name for builder in self.builders]
            }
        return await self._send_message(
            FlashbotsBuilder(), "mev_sendBundle", [bundle], True
        )

    async def titan_trace_bundle(self, bundle_hash: str | HexStr) -> dict:
        # TODO: When more builders enable bundle tracing, create a more generic version of this function
        return await self._send_message(
            TitanBuilder(),  # Always uses TitanBuilder, so create a titan builder obj regardless
            "titan_getBundleStats",
            [{"bundleHash": bundle_hash}],
            True,
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
