import json
from contextlib import asynccontextmanager
from enum import Enum

import websockets
from eth_rpc.exceptions import (
    ERPCRequestException, ERPCInvalidReturnException, ERPCSubscriptionException
)
from eth_rpc.common import Hex
from typing import List, Any
from eth_rpc.socket_pool import WebsocketPool
from eth_rpc.dclasses import Block, Sync, Receipt, Log


class BlockTag(str, Enum):
    """ Data type encapsulating all possible non-integer values for a DefaultBlock parameter
    API Documentation at: https://ethereum.org/en/developers/docs/apis/json-rpc/#default-block
    """
    earliest = "earliest"  # Genesis block
    latest = "latest"  # Last mined block
    pending = "pending"  # Pending state/transactions
    safe = "safe"  # Latest safe head block
    finalized = "finalized"  # Latest finalized block


DefaultBlock = int | BlockTag | str


class SubscriptionType(str, Enum):
    new_heads = "newHeads"
    logs = "logs"
    new_pending_transactions = "newPendingTransactions"
    syncing = "syncing"


def parse_results(res: str | dict, is_subscription: bool = False) -> Any:
    """
    Validates and parses the results of an RPC
    """
    if isinstance(res, str):
        res = json.loads(res)

    if isinstance(res, list):
        return [parse_results(item) for item in res]

    if is_subscription:
        # Subscription results are returned in a different format to normal calls
        res = res["params"]

    if "result" not in res:
        # Error case as no result is found
        if "error" in res:
            raise ERPCRequestException(res["error"]["code"], res["error"]["message"])
        else:
            raise ERPCInvalidReturnException("Invalid return value from ERPC, check your request.")

    return res["result"]


class Subscription:
    """
    A representation of a subscription to receive information from an ethereum endpoint
    Information is automatically decoded into an appropriate format upon being retrieved from the endpoint
    """
    def __init__(
            self,
            subscription_id: str,
            socket: websockets.WebSocketClientProtocol,
            subscription_type: SubscriptionType = SubscriptionType.new_heads
    ):
        self.subscription_id = subscription_id
        self.socket = socket

        # Selects the appropriate function to interpret the output of self.recv
        self.decode_function = {
            SubscriptionType.new_heads: self.new_heads_decoder,
            SubscriptionType.logs: self.logs_decoder,
            SubscriptionType.new_pending_transactions: self.new_pending_transactions_decoder,
            SubscriptionType.syncing: self.syncing_decoder
        }[subscription_type]

    async def recv(self) -> Block | Log | Hex | Sync:
        """
        infinite async generator function which will yield new information retrieved from a websocket
        """
        while True:
            res = await self.socket.recv()
            res = parse_results(res, is_subscription=True)
            yield self.decode_function(res)

    @staticmethod
    def new_heads_decoder(data: Any) -> Block:
        return Block.from_dict(data, infer_missing=True)

    @staticmethod
    def logs_decoder(data: Any) -> Log:
        return Log.from_dict(data, infer_missing=True)

    @staticmethod
    def new_pending_transactions_decoder(data: Any) -> Hex:
        return Hex(data)

    @staticmethod
    def syncing_decoder(data: Any) -> Sync:
        return Sync.from_dict(data)


class EthRPC:
    def __init__(self, url: str, pool_size: int = 5) -> None:
        self._id = 0
        self._pool = WebsocketPool(url, pool_size)

    def _next_id(self) -> None:
        self._id += 1

    @staticmethod
    def block_formatter(block_specifier: DefaultBlock | list[DefaultBlock] | tuple[DefaultBlock]) -> DefaultBlock | list[DefaultBlock]:
        """
        Automatically converts a DefaultBlock object to a format which can be sent via RPC
        DefaultBlock = int | BlockTsh | str
        integers are converted into their hex representation
        BlockTags are untouched as they are automatically converted into the appropriate strings later
        raw strings cannot be managed by this function and are ignored,
        it is expected that a provided string is either hex or the string representation of a block specifier
        """
        if isinstance(block_specifier, int):  # Converts integer values from DefaultBlock to hex for parsing
            block_specifier = hex(block_specifier)
        elif isinstance(block_specifier, list) or isinstance(block_specifier, tuple):
            # Converts integers in an iterable to hex and ignores others such as Block or str data types
            block_specifier = [hex(item) if isinstance(item, int) else item for item in block_specifier]
        return block_specifier

    def build_json(self, method: str, params: list[Any], increment: bool = True) -> str:
        """
        :param method: ethereum RPC method
        :param params: list of parameters to use in the function call, cast to string so Hex data may be used
        :param increment: Boolean determining whether self._id will be advanced after the json is built
        :return: json string converted with json.dumps
        This is slightly slower than raw string construction with fstrings, but more elegant
        """
        res = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": [param.hex_string if isinstance(param, Hex) else param for param in params],
            "id": self._id
        })
        if increment:
            self._next_id()
        return res

    def build_batch_json(self, method: str, param_list: list[list[Any]], increment: bool = True) -> str:
        """
        :param method: The ethereum JSON RPC method to be called
        :param param_list: A list of iterables of parameters to be appropriately formatted
        :param increment: If checked, this will increment the call id from this endpoint, on by default
        :return: Returns a stringified list of JSON objects
        """
        res = []
        for params in param_list:
            res.append({
                "jsonrpc": "2.0",
                "method": method,
                "params": [param.hex_string if isinstance(param, Hex) else param for param in params],
                "id": self._id
            })
            if increment:
                self._next_id()
        return json.dumps(res)

    @staticmethod
    def batch_format(*param_list: list[Any]) -> Any:
        """
        Automatically formats parameters for sending via build_batch_json
        """
        if all(isinstance(item, list) for item in param_list):
            return [item for item in zip(*param_list)]
        else:
            return param_list

    async def start_pool(self) -> None:
        """Exposes the ability to start the ERPC's socket pool before the first method call"""
        await self._pool.start()

    async def close_pool(self) -> None:
        """
        Closes the socket pool, this is important to not leave hanging open connections
        """
        await self._pool.quit()

    async def send_message(
            self,
            method: str,
            params: list[Any],
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> Any:
        """
        :param method: The ethereum JSON RPC procedure to be called
        :param params: A list of parameters to be passed for the RPC
        :param websocket: An optional external websocket for calls to this function

        Sends a message representing a call to a given method to this object's url
        """
        params = self.batch_format(*params)
        # json_builder is determined by whether a call is determined to be a batch or singular
        json_builder = self.build_batch_json if any(isinstance(param, tuple) for param in params) else self.build_json
        if websocket is None:
            # Gets a new websocket if one is not supplied to the function
            async with self._pool.get_socket() as ws:
                await ws.send(json_builder(method, params))
                msg = await ws.recv()
        else:
            # Sends a message with a given websocket
            await websocket.send(json_builder(method, params))
            msg = await websocket.recv()
        return parse_results(msg)

    @asynccontextmanager
    async def subscribe(self, method: SubscriptionType) -> Subscription:
        """
        :param method: The subscription's type, determined by a preset enum of possible types
        This function is decorated with an async context manager such that it can be used in an async with statement

        A subscription object is returned generated with a unique subscription id
        The subscription has a .recv() method to get the latest data returned by the ethereum endpoint
        for the given subscription.
        In the future a custom version of this function may be made to support custom subscription types.
        """
        async with self._pool.get_socket() as ws:
            subscription_id = ""
            try:
                subscription_id = await self.get_subscription(method, ws)
                sub = Subscription(
                    subscription_id=subscription_id,
                    socket=ws,
                    subscription_type=method
                )
                yield sub
            finally:
                if subscription_id == "":
                    raise ERPCSubscriptionException(f"Subscription of type {method.value} rejected by destination.")
                await self.unsubscribe(subscription_id, ws)

    async def get_subscription(
            self,
            method: SubscriptionType,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> str:
        """
        Supporting function for self.subscribe, opening a subscription for the provided websocket
        """
        msg = await self.send_message("eth_subscribe", [method.value], websocket)
        return msg

    async def unsubscribe(
            self,
            subscription_id: str | Hex,
            websocket: websockets.WebSocketClientProtocol | None = None
    ):
        """
        :param subscription_id: String subscription id returned by eth_subscribe
        :param websocket: An optional external websocket for calls to this function
        :return: The return of this function is not meant to be caught, though it does exist
        """
        msg = await self.send_message("eth_unsubscribe", [subscription_id], websocket)
        return msg

    async def get_block_number(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        cannot be batched
        :return: Integer number indicating the number of the most recently mined block
        """
        msg = await self.send_message("eth_blockNumber", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_transaction_count(
            self,
            address: str | Hex | list[str] | list[Hex],
            block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int | list[int]:
        """
        Gets the number of transactions sent from a given EOA address
        :param address: The address of an externally owned account
        :param block_specifier: A selector for a block, can be a specifier such as 'latest' or an integer block number
        :param websocket: An optional external websocket for calls to this function
        :return: Integer number of transactions
        """
        block_specifier = self.block_formatter(block_specifier)
        msg = await self.send_message("eth_getTransactionCount", [address, block_specifier], websocket)
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [int(result, 16) for result in msg]

    async def get_balance(
            self,
            contract_address: str | Hex | list[str] | list[Hex],
            block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int | list[int]:
        """
        Gets the balance of the account a given address points to
        :param contract_address: Contract address, its balance will be gotten at the block specified by quant_or_tag
        :param block_specifier: A selector for a block, can be a specifier such as 'latest' or an integer block number
        :param websocket: An optional external websocket for calls to this function
        :return: An integer balance in Wei of a given contract
        """
        block_specifier = self.block_formatter(block_specifier)
        msg = await self.send_message("eth_getBalance", [contract_address, block_specifier], websocket)
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [int(result, 16) for result in msg]

    async def get_gas_price(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Returns the current price per gas in Wei
        Cannot be batched
        :return: Integer number representing gas price in Wei
        """
        msg = await self.send_message("eth_gasPrice", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_block_by_number(
            self,
            block_specifier: DefaultBlock | list[DefaultBlock],
            full_object: bool | list[bool] = False,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> Block | list[Block] | None:
        """
        Returns a Block object which represents a block's state
        :param block_specifier: A specifier, either int or tag, delineating the block number to get
        :param full_object: Boolean specifying whether the desired return uses full transactions or transaction hashes
        :param websocket: An optional external websocket for calls to this function
        :return: A Block object representing blocks by either full transactions or transaction hashes
        """
        block_specifier = self.block_formatter(block_specifier)
        msg = await self.send_message("eth_getBlockByNumber", [block_specifier, full_object], websocket)
        if msg is None:
            return msg
        match msg:
            case None:
                return msg
            case dict():
                return Block.from_dict(msg, infer_missing=True)
            case _:
                return [Block.from_dict(result, infer_missing=True) for result in msg]

    async def get_block_by_hash(
            self,
            data: str | Hex | list[str] | list[Hex],
            full_object: bool | list[bool] = False,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> Block | list[Block]:
        """
        Returns a Block object which represents a block's state
        :param data: Hash of a block
        :param full_object: Boolean specifying whether the desired return uses full transactions or transaction hashes
        :param websocket: An optional external websocket for calls to this function
        :return: A Block object representing blocks by either full transactions or transaction hashes
        """
        msg = await self.send_message("eth_getBlockByHash", [data, full_object], websocket)
        match msg:
            case None:
                return msg
            case dict():
                return Block.from_dict(msg, infer_missing=True)
            case _:
                return [Block.from_dict(result, infer_missing=True) for result in msg]

    async def call(
            self,
            transaction: dict | list[dict],
            block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
            websocket: websockets.WebSocketClientProtocol | None = None
    ):
        """
        Executes a message call immediately without creating a transaction on the blockchain, useful for tests
        :param transaction: Full transaction call object, represented as a dict
            :key from: (OPTIONAL) The address a transaction is sent from
            :type: 20 Byte hex number

            :key to: The address a transaction is sent to
            :type: 20 Byte hex number

            :key gas: (OPTIONAL) Integer of gas provided for transaction execution
            :type: Hex int
                Note: eth_call consumes 0 gas but this may sometimes be necessary for other executions
                Note: gasPrice key is used for older blocks on the blockchain instead of the following two

            :key maxFeePerGas: (OPTIONAL) baseFeePerGas (determined by the network) + maxPriorityFeePerGas
            :type: Hex int

            :key maxPriorityFeePerGas: (OPTIONAL) Incentive fee you are willing to pay to ensure transaction execution
            :type: Hex int

            :key value: (OPTIONAL) Integer of the value sent with the transaction
            :type: Hex int

            :key data: (OPTIONAL) Hash of the method signature and encoded parameters
            :type: Hash (Ethereum contract ABI)

        :param block_specifier: A specifier, either int or tag, delineating the block number to execute the transaction
        :param websocket: An optional external websocket for calls to this function
        :return: Hex value of the executed contract
        """
        block_specifier = self.block_formatter(block_specifier)
        msg = await self.send_message("eth_call", [transaction, block_specifier], websocket)
        return msg

    async def get_transaction_receipt(
            self,
            tx_hash: str | Hex | list[str] | list[Hex],
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> Receipt | list[Receipt]:
        """
        Gets the receipt of a transaction given its hash, the definition of a receipt can be seen in dclasses.py
        """
        msg = await self.send_message("eth_getTransactionReceipt", [tx_hash], websocket)
        if msg is None:
            return msg
        match msg:
            case None:
                return msg
            case dict():
                return Receipt.from_dict(msg, infer_missing=True)
            case _:
                return [Receipt.from_dict(result, infer_missing=True) for result in msg]

    async def send_raw_transaction(
            self,
            raw_transaction: str | Hex | list[str] | list[Hex],
            websocket: websockets.WebSocketClientProtocol | None = None
    ):
        """
        Returns the receipt of a transaction by transaction hash
        :param raw_transaction: The hash of a transaction
        :param websocket: An optional external websocket for calls to this function
        :type: 32 Byte Hex
        :return: Transaction receipt object of the following shape
            :key transactionHash: Hash of the transaction
            :type: 32 Byte Hex

            :key transactionIndex: Integer of the transaction's index position in it's executing block
            :type: Hex Int

            :key blockHash: Hash of the block the transaction was executed in
            :type: 32 Byte Hex

            :key blockNumber: Block number the transaction was executed in
            :type: Hex Int

            :key from: Address of the sender
            :type: 20 Byte Hex Address

            :key to: Address of the receiver. Can be null when the transaction creates a contract.
            :type: 20 Byte Hex Address

            :key cumulativeGasUsed: Total gas used when the transaction was executed in the block
            :type: Hex Int

            :key effectiveGasPrice: Base fee + tip paid per unit gas used
            :type: Hex Int

            :key gasUsed: The amount of gas used by this specific transaction alone
            :type: Hex Int

            :key contractAddress: Address value of created contract if the transaction created a contract
            :type: 20 Byte Hex Address

            :key logs: Array of log objects generated by this transaction
            :type: Array

            :key logsBloom: Bloom filter for light clients to quickly retrieve logs
            :type: 256 Byte Hex

            :key type: Transaction type
                0x0: Legacy transaction
                0x1: Access list type
                0x2: Dynamic fee
            :type: Hex Int

            One of the following two will be included:

            :key root: Post transaction stateroot
            :type: 32 Byte Hex

            :key status: Either 0x1 for success or 0x0 for failure
            :type: Hex Int
        """
        msg = await self.send_message("eth_sendRawTransaction", [raw_transaction], websocket)
        return msg

    async def send_transaction(
            self,
            transaction: dict | list[dict],
            websocket: websockets.WebSocketClientProtocol | None = None
    ):
        """
        Creates a new message call transaction or contract creation
        :param transaction: Built transaction object, formed as a dict with the following keys
            :key from: The address the transaction is sent from
            :type: 20 Byte Hex Address

            :key to: (OPTIONAL WHEN CREATING CONTRACT) The address the transaction is directed to
            :type: 20 Byte Hex Address

            :key gas: (OPTIONAL) Integer of gas provided for transaction execution
            :type: Hex int
                Note: Unused gas will be returned
                Note: gasPrice key is used for older blocks on the blockchain instead of the following two

            :key maxFeePerGas: (OPTIONAL) baseFeePerGas (determined by the network) + maxPriorityFeePerGas
            :type: Hex int

            :key maxPriorityFeePerGas: (OPTIONAL) Incentive fee you are willing to pay to ensure transaction execution
            :type: Hex int

            :key value: (OPTIONAL) Integer of the value sent with the transaction
            :type: Hex int

            :key data: Compiled contract code OR the hash of the invoked method signature with its encoded params
            :type: Hash (Ethereum contract ABI)

            :key nonce: (OPTIONAL) Integer of a nonce.
            This allows overwriting your pending transactions with the same nonce
            :type: Hex Int
        :param websocket: An optional external websocket for calls to this function
        :return: Transaction hash (or zero hash if the transaction is not yet available)
        :type: 32 Byte Hex
        """
        msg = await self.send_message("eth_sendTransaction", [transaction], websocket)
        return msg

    async def get_protocol_version(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        msg = await self.send_message("eth_protocolVersion", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg)

    async def get_sync_status(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool | Sync:
        msg = await self.send_message("eth_syncing", [], websocket)
        match msg:
            case None:
                return msg
            case "false":
                return False
            case _:
                return Sync.from_dict(msg, infer_missing=True)

    async def get_coinbase(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> str | Hex:
        msg = await self.send_message("eth_coinbase", [], websocket)
        return msg

    async def get_chain_id(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        msg = await self.send_message("eth_chainId", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def is_mining(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool:
        msg = await self.send_message("eth_mining", [], websocket)
        return msg

    async def get_hashrate(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        msg = await self.send_message("eth_hashrate", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_accounts(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> List[str | Hex]:
        msg = await self.send_message("eth_accounts", [], websocket)
        return msg
