import asyncio
import json
from abc import ABC
from typing import Any
import aiohttp

from eth_account import Account, messages
from eth_utils import keccak
from pythereum.rpc import parse_results
from pythereum.common import HexStr
from pythereum.dclasses import Bundle, MEVBundle
from pythereum.exceptions import ERPCBuilderException, ERPCRequestException


class Builder(ABC):
    def __init__(
            self,
            url: str,
            private_transaction_method: str = "eth_sendPrivateTransaction",
            bundle_method: str = "eth_sendBundle",
            cancel_bundle_method: str = "eth_cancelBundle",
            mev_bundle_method: str = "mev_sendBundle",
            bundle_params: set = None,
            private_key: str = None
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
        self.mev_bundle_method = mev_bundle_method
        self.private_key = HexStr(private_key) if private_key is not None else None
        super().__init__()

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx, max_block_number]

    def format_bundle(self, bundle: dict | Bundle) -> dict:
        return {key: bundle[key] for key in bundle.keys() & self.bundle_params}

    def format_mev_bundle(self, bundle: MEVBundle) -> list[dict]:
        return [bundle]

    def get_header(self, data: Any = None) -> Any:
        return None

    def get_flashbots_header(self, payload: str = "") -> dict:
        payload = messages.encode_defunct(keccak(text=payload))
        return {"X-Flashbots-Signature": f"{Account.from_key(self.private_key.hex_bytes).address}:"
                                         f"{Account.sign_message(payload, self.private_key.hex_bytes).signature.hex()}"}


class TitanBuilder(Builder):
    def __init__(self, private_key: str | HexStr | None = None):
        super().__init__(
            "https://rpc.titanbuilder.xyz",
            "eth_sendPrivateTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "mev_sendBundle",
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
            },
            private_key
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
    def __init__(self, private_key: str | HexStr | None = None):
        super().__init__(
            "https://rpc.beaverbuild.org/",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "mev_sendBundle",
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
            },
            private_key
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx]


class RsyncBuilder(Builder):
    def __init__(self, private_key: str | HexStr | None = None):
        super().__init__(
            "https://rsync-builder.xyz/",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "mev_sendBundle",
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
            },
            private_key
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx]


class Builder0x69(Builder):
    def __init__(self, private_key: str | HexStr | None = None):
        super().__init__(
            "https://builder0x69.io/",
            "eth_sendRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "mev_sendBundle",
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
            },
            private_key
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx]


class FlashbotsBuilder(Builder):
    def __init__(self, private_key: str | HexStr | None = None):
        super().__init__(
            "https://relay.flashbots.net",
            "eth_sendPrivateRawTransaction",
            "eth_sendBundle",
            "eth_cancelBundle",
            "mev_sendBundle",
            {
                "txs",
                "blockNumber",
                "minTimestamp",
                "maxTimestep",
                "revertingTxHashes",
                "replacementUuid"
            },
            private_key
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
    def __init__(
            self,
            builders: Builder | list[Builder],
            private_key: str | bytes | HexStr | list[str] | list[bytes] | list[HexStr] = None
    ):
        if not isinstance(builders, list):
            builders = [builders]
        self.builders = builders
        if isinstance(private_key, list):
            for key, builder in zip(private_key, self.builders):
                builder.private_key = HexStr(key)
        elif private_key is not None:
            for builder in self.builders:
                builder.private_key = HexStr(private_key)
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
            use_flashbots_signature: bool = False
    ):
        if self.session is not None:
            constructed_json = self._build_json(method, params)
            header_data = builder.get_flashbots_header(
                json.dumps(constructed_json)
            ) if use_flashbots_signature else builder.get_header(json.dumps(constructed_json))
            async with self.session.post(
                    builder.url,
                    json=constructed_json,
                    headers=header_data
            ) as resp:
                if resp.status != 200:
                    raise ERPCRequestException(
                        resp.status,
                        f"Invalid BuilderRPC request for url {builder.url} of form "
                        f"(method={method}, params={params})"
                    )

                msg = await resp.json()
        else:
            raise ERPCBuilderException(
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
        tx_methods = [builder.private_transaction_method for builder in self.builders]
        tx = [builder.format_private_transaction(tx, extra_info) for builder in self.builders]
        return await asyncio.gather(
            *(self._send_message(builder, method, transaction) for builder, method, transaction in
              zip(self.builders, tx_methods, tx))
        )

    async def send_bundle(
            self,
            bundle: Bundle,
    ) -> Any:
        tx_methods = [builder.bundle_method for builder in self.builders]
        tx = [builder.format_bundle(bundle) for builder in self.builders]
        return await asyncio.gather(
            *(self._send_message(builder, method, transaction) for builder, method, transaction in
              zip(self.builders, tx_methods, tx))
        )

    async def cancel_bundle(
            self,
            replacement_uuids: str | HexStr,
    ):
        cancel_methods = [builder.cancel_bundle_method for builder in self.builders]
        replacement_uuids = [replacement_uuids for _ in self.builders]
        return await asyncio.gather(
            *(self._send_message(builder, method, uuid) for builder, method, uuid in
              zip(self.builders, cancel_methods, replacement_uuids))
        )

    async def send_mev_bundle(
            self,
            bundle: MEVBundle
    ) -> Any:
        mev_methods = [builder.mev_bundle_method for builder in self.builders]
        bundles = [builder.format_mev_bundle(bundle) for builder in self.builders]
        return await asyncio.gather(
            *(self._send_message(builder, method, bundle, True) for builder, method, bundle in
              zip(self.builders, mev_methods, bundles))
        )

    async def __aenter__(self):
        await self.start_session()
        return self

    async def __aexit__(self, *args):
        await self.close_session()


# A list containing all the current supported builders. Can be passed in to a BuilderRPC to send to all
ALL_BUILDERS = [TitanBuilder(), Builder0x69(), RsyncBuilder(), BeaverBuilder(), FlashbotsBuilder()]
