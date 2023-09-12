import asyncio
import json
from abc import ABC
from typing import Any
import aiohttp

from eth_account import Account, messages
from eth_utils import keccak
from pythereum.rpc import parse_results
from pythereum.common import HexStr
from pythereum.dclasses import Bundle
from pythereum.exceptions import ERPCBuilderException, ERPCRequestException


class Builder(ABC):
    def __init__(
            self,
            url: str | HexStr,
            private_transaction_method: str | HexStr = "eth_sendPrivateTransaction",
            bundle_method: str | HexStr = "eth_sendBundle",
            cancel_bundle_method: str | HexStr = "eth_cancelBundle",
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
                "refundTxHashes"
            }

        self.url = url
        self.private_transaction_method = private_transaction_method
        self.bundle_method = bundle_method
        self.cancel_bundle_method = cancel_bundle_method
        self.bundle_params = bundle_params
        super().__init__()

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx, max_block_number]

    def format_bundle(self, bundle: dict | Bundle) -> dict:
        return {key: bundle[key] for key in bundle.keys() & self.bundle_params}

    def get_header(self, data: Any = None) -> Any:
        return None


class TitanBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://rpc.titanbuilder.xyz",
            "eth_sendPrivateTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundIndex"
                "refundRecipient",
            }
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
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
            "eth_cancelBundle",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
                "refundTxHashes"
            }
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx]


class RsyncBuilder(Builder):
    def __init__(self):
        super().__init__(
            "https://rsync-builder.xyz/",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
                "refundTxHashes"
            }
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx]


class Builder0x69(Builder):
    def __init__(self):
        super().__init__(
            "https://builder0x69.io/",
            "eth_sendRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestamp",
                "revertingTxHashes",
                "uuid"
                "replacementUuid",
                "refundPercent",
                "refundRecipient",
            }
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx]


class FlashbotsBuilder(Builder):
    def __init__(self, private_key: str | HexStr):
        self.private_key = HexStr(private_key)
        super().__init__(
            "https://relay.flashbots.net",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestep",
                "revertingTxHashes",
                "replacementUuid"
            },
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            preferences: dict = None
    ) -> list[Any]:
        return [{"tx": tx, "preferences": preferences}]

    def get_header(self, payload: str = "") -> dict:
        payload = messages.encode_defunct(keccak(text=payload))
        return {"X-Flashbots-Signature": f"{Account.from_key(self.private_key.hex_bytes).address}:"
                                         f"{Account.sign_message(payload, self.private_key.hex_bytes).signature.hex()}"}


class BuilderRPC:
    """
    An RPC class designed for sending raw transactions and bundles to specific block builders
    """
    def __init__(self, builders: Builder | list[Builder]):
        if isinstance(builders, list):
            if len(builders) == 1:
                builders = builders[0]
        self.builder = builders
        self.session = None
        self._id = 0

    def _next_id(self) -> None:
        self._id += 1

    def _build_json(
        self, method: str, params: list[Any], increment: bool = True
    ) -> dict:
        """
        :param method: ethereum RPC method
        :param params: list of parameters to use in the function call, cast to string so Hex data may be used
        :param increment: Boolean determining whether self._id will be advanced after the json is built
        :return: json dictionary
        This is slightly slower than raw string construction with fstrings, but more elegant
        """
        res = {"jsonrpc": "2.0", "method": method, "params": params, "id": self._id}

        if increment:
            self._next_id()
        return res

    async def _send_message(self, method: str | list[str], params: list[Any]):
        if self.session is not None:
            if isinstance(self.builder, list):
                msg = await asyncio.gather(
                    *(self._post(mth, param, builder) for mth, param, builder in zip(method, params, self.builder))
                )
                self._next_id()
            else:
                msg = await self._post(method, params, self.builder)
                self._next_id()
        else:
            raise ERPCBuilderException(
                "BuilderRPC session not started. Either context manage this class or call BuilderRPC.start_session()"
            )

        return parse_results(msg)

    async def _post(self, method: str, params: list[Any], builder: Builder) -> Any:
        constructed_json = self._build_json(method, params, increment=False)
        async with self.session.post(
                builder.url,
                json=constructed_json,
                headers=builder.get_header(json.dumps(constructed_json))
        ) as resp:
            if resp.status != 200:
                raise ERPCRequestException(
                    resp.status,
                    f"Invalid BuilderRPC request for url {builder.url} of form "
                    f"(method={method}, params={params})"
                )

            msg = await resp.json()
        return msg

    async def start_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def send_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            extra_info: Any = None,
    ) -> Any:
        if isinstance(self.builder, list):
            transaction = [builder.format_private_transaction(tx, extra_info) for builder in self.builder]
            tx_method = [builder.private_transaction_method for builder in self.builder]
        else:
            transaction = [self.builder.format_private_transaction(tx, extra_info)]
            tx_method = self.builder.private_transaction_method
        return await self._send_message(tx_method, transaction)

    async def send_bundle(
            self,
            bundle: Bundle | list[Bundle],
    ) -> HexStr | list[HexStr]:
        if isinstance(self.builder, list):
            transaction = [builder.format_bundle(bundle) for builder in self.builder]
            tx_method = [builder.bundle_method for builder in self.builder]
        else:
            transaction = [self.builder.format_bundle(bundle)]
            tx_method = self.builder.bundle_method
        return await self._send_message(tx_method, transaction)

    async def cancel_bundle(
            self,
            replacement_uuid: str | HexStr | list[str] | list[HexStr],
    ):
        if isinstance(self.builder, list):
            cancel_method = [builder.cancel_bundle_method for builder in self.builder]
        else:
            cancel_method = self.builder.cancel_bundle_method
            replacement_uuid = [replacement_uuid]
        return await self._send_message(cancel_method, replacement_uuid)

    async def __aenter__(self):
        await self.start_session()
        return self

    async def __aexit__(self, *args):
        await self.close_session()


# A list containing all the current supported builders. Can be passed in to a BuilderRPC to send to all
ALL_BUILDERS = [TitanBuilder(), Builder0x69(), RsyncBuilder(), BeaverBuilder()]
