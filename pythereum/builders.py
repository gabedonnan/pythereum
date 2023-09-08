from abc import ABC
from typing import Any

from pythereum import HexStr, EthRPC, Bundle


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
