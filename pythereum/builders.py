from abc import ABC
from typing import Any

import websockets

from pythereum.common import HexStr
from pythereum.rpc import EthRPC, Bundle


class Builder(ABC):
    def __init__(
            self,
            url: str | HexStr,
            private_transaction_method: str | HexStr = "eth_sendPrivateTransaction",
            bundle_method: str | HexStr = "eth_sendBundle",
            cancel_bundle_method: str | HexStr = "eth_cancelBundle",
            bundle_params: set = None,
            header: dict = None
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
        self.header = header
        super().__init__()

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            max_block_number: str | HexStr | list[str] | list[HexStr] | None = None
    ) -> list[Any]:
        return [tx, max_block_number]

    def format_bundle(self, bundle: dict | Bundle) -> dict:
        return {key: bundle[key] for key in bundle.keys() & self.bundle_params}


class TitanBuilder(Builder):
    def __init__(self):
        super().__init__(
            "wss://rpc.titanbuilder.xyz",
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
    ) -> list[Any]:
        res = {"tx": tx}
        if max_block_number is not None:
            res["maxBlockNumber"] = max_block_number
        return [res]


class BeaverBuilder(Builder):
    def __init__(self):
        super().__init__(
            "wss://rpc.beaverbuild.org/",
            "eth_sendPrivateTransaction"
        )


class RsyncBuilder(Builder):
    def __init__(self):
        super().__init__(
            "wss://rsync-builder.xyz/",
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
            "wss://builder0x69.io/",
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
    def __init__(self, wallet_address: str, signed_payload: str):
        super().__init__(
            "wss://relay.flashbots.net",
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
            {"X-Flashbots-Signature": f"{wallet_address}:{signed_payload}"}
        )

    def format_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            preferences: dict = None
    ) -> list[Any]:
        return [{"tx": tx, "preferences": preferences}]


class BuilderRPC:
    """
    An RPC class designed for sending raw transactions and bundles to specific block builders
    """
    def __init__(self, builder: Builder, pool_size: int = 1):
        self.builder = builder
        self.rpc = EthRPC(builder.url, pool_size)

    async def start_pool(self):
        await self.rpc.start_pool()

    async def close_pool(self):
        await self.rpc.close_pool()

    async def send_private_transaction(
            self,
            tx: str | HexStr | list[str] | list[HexStr],
            extra_info: Any = None,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> Any:
        transaction = self.builder.format_private_transaction(tx, extra_info)
        if self.builder.header is not None and websocket is not None:
            # Builders like Flashbots require signed headers to identify the sender.
            # This unfortunately means we must open new websockets for now as my websocket pools do not support headers
            async with websockets.connect(self.builder.url, extra_headers=self.builder.header) as ws:
                return await self.rpc.send_raw(self.builder.private_transaction_method, [transaction], ws)
        else:
            return await self.rpc.send_raw(self.builder.private_transaction_method, [transaction], websocket)

    async def send_bundle(
            self,
            bundle: Bundle | list[Bundle],
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> HexStr | list[HexStr]:
        bundle = self.builder.format_bundle(bundle)
        if self.builder.header is not None and websocket is not None:
            async with websockets.connect(self.builder.url, extra_headers=self.builder.header) as ws:
                await self.rpc.send_raw(self.builder.bundle_method, [bundle], ws)
        else:
            return await self.rpc.send_raw(self.builder.bundle_method, [bundle], websocket)

    async def cancel_bundle(
            self,
            replacement_uuid: str | HexStr | list[str] | list[HexStr],
            websocket: websockets.WebSocketClientProtocol | None = None
    ):
        if self.builder.header is not None and websocket is not None:
            async with websockets.connect(self.builder.url, extra_headers=self.builder.header) as ws:
                return await self.rpc.send_raw(self.builder.cancel_bundle_method, [replacement_uuid], ws)
        else:
            return await self.rpc.send_raw(self.builder.cancel_bundle_method, [replacement_uuid], websocket)

    async def __aenter__(self):
        await self.start_pool()
        return self

    async def __aexit__(self, *args):
        await self.close_pool()
