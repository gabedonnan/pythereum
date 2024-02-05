# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any
from aiohttp import ClientSession
import websockets
from pythereum.socket_pool import WebsocketPool
from pythereum.exceptions import (
    PythereumRequestException,
    PythereumInvalidReturnException,
    PythereumSubscriptionException,
    PythereumManagerException,
)
from pythereum.common import (
    HexStr,
    BlockTag,
    DefaultBlock,
    SubscriptionType,
)
from pythereum.dclasses import (
    Block,
    Sync,
    Receipt,
    Log,
    Transaction,
    TransactionFull,
    FeeHistory,
    Proof,
    MempoolInfo,
)


def parse_results(
    res: str | dict, is_subscription: bool = False, builder: str = None
) -> Any:
    """
    Validates and parses the results of an RPC
    """
    if isinstance(res, str):
        res = json.loads(res)

    if isinstance(res, list):
        return [parse_results(item) for item in res]

    if is_subscription and "params" in res:
        # Subscription results are returned in a different format to normal calls
        res = res["params"]

    if "result" not in res:
        # Error case as no result is found
        if "error" in res:
            errmsg = res["error"]["message"] + (
                "" if builder is None else f" for builder {builder}"
            )
            raise PythereumRequestException(res["error"]["code"], errmsg)
        else:
            raise PythereumInvalidReturnException(
                f"Invalid return value from RPC, return format: {res}"
            )

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
        subscription_type: SubscriptionType = SubscriptionType.new_heads,
        max_message_num: int = -1,
    ):
        self.subscription_id = subscription_id
        self.socket = socket
        self.max_message_num = max_message_num

        # Selects the appropriate function to interpret the output of self.recv
        self.decode_function = {
            SubscriptionType.new_heads: self.new_heads_decoder,
            SubscriptionType.logs: self.logs_decoder,
            SubscriptionType.new_pending_transactions: self.new_pending_transactions_decoder,
            SubscriptionType.syncing: self.syncing_decoder,
        }[subscription_type]

    async def recv(self) -> Block | Log | HexStr | Sync:
        """
        infinite async generator function which will yield new information retrieved from a websocket
        """
        counter = 0
        while self.max_message_num == -1 or counter < self.max_message_num:
            res = await self.socket.recv()
            res = parse_results(res, is_subscription=True)
            counter += 1
            yield self.decode_function(res)

    @staticmethod
    def new_heads_decoder(data: Any) -> Block:
        """
        Decodes the outputs for a new heads subscription
        """
        return Block.from_dict(data, infer_missing=True)

    @staticmethod
    def logs_decoder(data: Any) -> Log:
        """
        Decodes the outputs for a logs subscription
        """
        return Log.from_dict(data, infer_missing=True)

    @staticmethod
    def new_pending_transactions_decoder(data: Any) -> HexStr:
        """
        Decodes the outputs for a new pending transactions subscription
        """
        return HexStr(data)

    @staticmethod
    def syncing_decoder(data: Any) -> Sync:
        """
        Decodes the outputs for a syncing status subscription
        """
        return Sync.from_dict(data)


class NonceManager:
    """
    Manages the nonces of addresses for the purposes of constructing transactions,
    requires an RPC connection in order to get starting transaction counts for each address.

    This currently operates assuming no other sources are creating transactions from a given address.
    """

    def __init__(self, rpc: "EthRPC | str | None" = None):
        if isinstance(rpc, str):
            rpc = EthRPC(rpc, 1)
        self.rpc = rpc
        self.nonces = {}
        self._close_pool = True

    def __getitem__(self, key):
        return self.nonces[HexStr(key)]

    def __setitem__(self, key, value):
        self.nonces[HexStr(key)] = value

    async def __aenter__(self):
        if self.rpc is not None:
            if not self.rpc.pool_connected():
                await self.rpc.start_pool()
            else:
                self._close_pool = False
        else:
            raise PythereumManagerException(
                "NonceManager was never given EthRPC or RPC Url instance"
            )
        return self

    async def __aexit__(self, *args):
        if self._close_pool:
            await self.rpc.close_pool()

    async def next_nonce(self, address: str | HexStr) -> int:
        """
        Get the next nonce for a transaction from a given address
        """
        address = HexStr(address)
        if self.rpc is not None and address not in self.nonces:
            self.nonces[address] = await self.rpc.get_transaction_count(
                address, BlockTag.latest
            )
        else:
            self.nonces[address] += 1
        return self.nonces[address]

    async def fill_transaction(
        self, tx: dict | Transaction | list[dict] | list[Transaction]
    ) -> None:
        """
        This function mutates input transaction dictionaries such that they are filled with the correct nonce values
        """
        if isinstance(tx, list):
            for sub_tx in tx:
                # If elements in a list are references to the same list this will not work properly
                sub_tx["nonce"] = HexStr(await self.next_nonce(sub_tx["from"]))
        elif tx is not None:
            tx["nonce"] = HexStr(await self.next_nonce(tx["from"]))


class EthRPC:
    """
    A class managing communication with an Ethereum node via the Ethereum JSON RPC API.
    """

    def __init__(
        self,
        url: str,
        pool_size: int = 5,
        use_socket_pool: bool = True,
        connection_max_payload_size: int = 2**20,
        connection_timeout: int = 20,
    ) -> None:
        """
        :param url: URL for the ethereum node to connect to
        :param pool_size: The number of websocket connections opened for the WebsocketPool
        :param use_socket_pool: Whether the socket pool should be used or AIOHTTP requests
        :param connection_max_payload_size: The maximum payload size a websocket can send or recv in one message
        :param connection_timeout: The maximum time in seconds to wait for a response from the websocket before timeout
        """
        self._id = 0
        if use_socket_pool:
            self._pool = WebsocketPool(
                url, pool_size, connection_max_payload_size, connection_timeout
            )
        else:
            self._pool = None
            self.session = ClientSession()
        self._http_url = url.replace("wss://", "https://").replace("ws://", "http://")

    def _next_id(self) -> None:
        """
        Increments the internal ID by 1, used for nonces
        """
        self._id += 1

    async def __aenter__(self):
        await self.start_pool()
        return self

    async def __aexit__(self, *args):
        await self.close_pool()

    @staticmethod
    def _filter_option_formatter(
        from_block: DefaultBlock | list[DefaultBlock],
        to_block: DefaultBlock | list[DefaultBlock],
        address: str
        | HexStr
        | list[str]
        | list[HexStr]
        | list[list[str]]
        | list[list[HexStr]],
        topics: str | HexStr | list[str] | list[HexStr],
    ) -> dict | list[dict]:
        """
        Converts a given set of filter options into either a dictionary or list of dictionaries to be passed to the RPC
        """
        if all(
            isinstance(param, list) for param in (from_block, to_block, address, topics)
        ):
            # Detects whether a set of filter options is batched
            return [
                {"fromBlock": f, "toBlock": t, "address": a, "topics": tpc}
                for (f, t, a, tpc) in zip(from_block, to_block, address, topics)
            ]
        else:
            # Non-batched object return
            return {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": address,
                "topics": topics,
            }

    @staticmethod
    def _block_formatter(
        block_specifier: DefaultBlock | list[DefaultBlock] | tuple[DefaultBlock],
    ) -> DefaultBlock | list[DefaultBlock]:
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
            block_specifier = [
                hex(item) if isinstance(item, int) else item for item in block_specifier
            ]
        return block_specifier

    def _build_json(
        self, method: str, params: list[Any], increment: bool = True
    ) -> str:
        """
        :param method: ethereum RPC method
        :param params: list of parameters to use in the function call, cast to string so Hex data may be used
        :param increment: Boolean determining whether self._id will be advanced after the json is built
        :return: json string converted with json.dumps
        This is slightly slower than raw string construction with fstrings, but more elegant
        """
        res = json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params, "id": self._id}
        )
        if increment:
            self._next_id()
        return res

    def _build_batch_json(
        self, method: str, param_list: list[list[Any]], increment: bool = True
    ) -> str:
        """
        :param method: The ethereum JSON RPC method to be called
        :param param_list: A list of iterables of parameters to be appropriately formatted
        :param increment: If checked, this will increment the call id from this endpoint, on by default
        :return: Returns a stringified list of JSON objects
        """
        res = []
        for params in param_list:
            res.append(
                {"jsonrpc": "2.0", "method": method, "params": params, "id": self._id}
            )
            if increment:
                self._next_id()
        return json.dumps(res)

    @staticmethod
    def _batch_format(*param_list: list[Any]) -> Any:
        """
        Automatically formats parameters for sending via build_batch_json
        """
        if all(isinstance(item, list) for item in param_list):
            return list(zip(*param_list))
        else:
            return param_list

    def pool_connected(self) -> bool:
        """
        Returns a boolean indicating whether the socket pool is connected to an endpoint
        """
        if self._pool is None:
            return False
        else:
            return self._pool.connected

    async def start_pool(self) -> None:
        """
        Exposes the ability to start the ERPC's socket pool before the first method call
        """
        if self._pool is not None:
            await self._pool.start()
        else:
            if not self.session.closed:
                await self.session.close()
            self.session = ClientSession()

    async def close_pool(self) -> None:
        """
        Closes the socket pool, this is important to not leave hanging open connections
        """
        if self._pool is not None:
            await self._pool.quit()
        else:
            await self.session.close()

    async def _send_message(
        self,
        method: str,
        params: list[Any],
        websocket: websockets.WebSocketClientProtocol | None = None,
        is_subscription: bool = False,
    ) -> Any:
        """
        :param method: The ethereum JSON RPC procedure to be called
        :param params: A list of parameters to be passed for the RPC
        :param websocket: An optional external websocket for calls to this function
        :param is_subscription: A boolean defining whether a result should be decoded as a subscription

        Sends a message representing a call to a given method to this object's url
        """
        params = self._batch_format(*params)
        # json_builder is determined by whether a call is determined to be a batch or singular
        built_msg = (
            self._build_batch_json(method, params)
            if any(isinstance(param, tuple) for param in params)
            else self._build_json(method, params)
        )

        if websocket is None:
            # Gets a new websocket if one is not supplied to the function
            if self._pool is not None:
                # Using websocket pool
                async with self._pool.get_socket() as ws:
                    await ws.send(built_msg)
                    msg = await ws.recv()
            else:
                msg = await self._send_message_aio(built_msg)
        else:
            # Using a given websocket
            await websocket.send(built_msg)
            msg = await websocket.recv()
        return parse_results(msg, is_subscription)

    async def _send_message_aio(self, built_msg: str) -> dict:
        """
        Sends a message with aiohttp and returns a dict
        """
        async with self.session.post(
            url=self._http_url,
            data=built_msg,
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status != 200:
                raise PythereumRequestException(
                    resp.status,
                    f"Bad EthRPC aiohttp request for url {self._http_url} of form {built_msg}",
                )
            msg = await resp.json()
        return msg

    @asynccontextmanager
    async def subscribe(self, method: SubscriptionType, max_message_num: int = -1) -> Subscription:
        """
        :param method: The subscription's type, determined by a preset enum of possible types
        :param max_message_num: The maximum number of messages the subscription can receive,
            default -1 for infinite subscription.
            Eventually this will be replaced with a fleshed out filter to cancel subscriptions based on conditions.

        This function is decorated with an async context manager such that it can be used in an async with statement

        A subscription object is returned generated with a unique subscription id
        The subscription has a .recv() method to get the latest data returned by the ethereum endpoint
        for the given subscription.
        In the future a custom version of this function may be made to support custom subscription types.
        """
        async with self._pool.get_socket() as ws:
            subscription_id = ""
            try:
                subscription_id = await self._get_subscription(method, ws)
                sub = Subscription(
                    subscription_id=subscription_id,
                    socket=ws,
                    subscription_type=method,
                    max_message_num=max_message_num,
                )
                yield sub
            finally:
                if subscription_id == "":
                    raise PythereumSubscriptionException(
                        f"Subscription of type {method.value} rejected by destination."
                    )
                await self._unsubscribe(subscription_id, ws)

    # Public RPC methods

    async def _get_subscription(
        self,
        method: SubscriptionType,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> str:
        """
        Supporting function for self.subscribe, opening a subscription for the provided websocket
        """
        return await self._send_message("eth_subscribe", [method.value], websocket)

    async def _unsubscribe(
        self,
        subscription_id: str | HexStr,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ):
        """
        :param subscription_id: String subscription id returned by eth_subscribe
        :param websocket: An optional external websocket for calls to this function
        :return: The return of this function is not meant to be caught, though it does exist
        """
        msg = await self._send_message(
            "eth_unsubscribe", [subscription_id], websocket, True
        )
        return msg

    async def get_block_number(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        :return: Integer number indicating the number of the most recently formed block
        """
        msg = await self._send_message("eth_blockNumber", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_transaction_count(
        self,
        address: str | HexStr | list[str] | list[HexStr],
        block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Gets the number of transactions sent from a given EOA address
        :param address: The address of an externally owned account
        :param block_specifier: A selector for a block, can be a specifier such as 'latest' or an integer block number
        :param websocket: An optional external websocket for calls to this function
        :return: Integer number of transactions
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getTransactionCount", [address, block_specifier], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_balance(
        self,
        contract_address: str | HexStr | list[str] | list[HexStr],
        block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Gets the balance of the account a given address points to
        :param contract_address: Contract address, its balance will be gotten at the block specified by quant_or_tag
        :param block_specifier: A selector for a block, can be a specifier such as 'latest' or an integer block number
        :param websocket: An optional external websocket for calls to this function
        :return: An integer balance in Wei of a given contract
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getBalance", [contract_address, block_specifier], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_gas_price(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Returns the current price per gas in Wei
        :return: Integer number representing gas price in Wei
        """
        msg = await self._send_message("eth_gasPrice", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_block_by_number(
        self,
        block_specifier: DefaultBlock | list[DefaultBlock],
        full_object: bool | list[bool] = True,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Block | list[Block] | None:
        """
        Returns a Block object which represents a block's state
        :param block_specifier: A specifier, either int or tag, delineating the block number to get
        :param full_object: Boolean specifying whether the desired return uses full transactions or transaction hashes
        :param websocket: An optional external websocket for calls to this function
        :return: A Block object representing blocks by either full transactions or transaction hashes
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getBlockByNumber", [block_specifier, full_object], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return Block.from_dict(msg, infer_missing=True)
            case _:
                return [Block.from_dict(result, infer_missing=True) for result in msg]

    async def get_block_by_hash(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        full_object: bool | list[bool] = True,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Block | list[Block]:
        """
        Returns a Block object which represents a block's state
        :param data: Hash of a block
        :param full_object: Boolean specifying whether the desired return uses full transactions or transaction hashes
        :param websocket: An optional external websocket for calls to this function
        :return: A Block object representing blocks by either full transactions or transaction hashes
        """
        msg = await self._send_message(
            "eth_getBlockByHash", [data, full_object], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return Block.from_dict(msg, infer_missing=True)
            case _:
                return [Block.from_dict(result, infer_missing=True) for result in msg]

    async def call(
        self,
        transaction: dict | Transaction | list[dict] | list[Transaction],
        block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ):
        """
        Executes a message call immediately without creating a transaction on the blockchain, useful for tests
        :param transaction: Transaction call object, represented as a dict or Transaction object
        :param block_specifier: A specifier, either int or tag, delineating the block number to execute the transaction
        :param websocket: An optional external websocket for calls to this function
        :return: Hex value of the executed contract
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_call", [transaction, block_specifier], websocket
        )
        return msg

    async def get_transaction_receipt(
        self,
        tx_hash: str | HexStr | list[str] | list[HexStr],
        retries: int = 0,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Receipt | list[Receipt]:
        """
        Gets the receipt of a transaction given its hash, the definition of a receipt can be seen in dclasses.py

        :param tx_hash: Hash of the transaction from which the receipt should be derived
        :param retries: (Optional) The maximum number of retries to attempt until receipt has been generated
        :param websocket: (Optional) external websocket for calls to this function
        :return: Transaction receipt object or list of transaction receipts
        """
        msg = await self._send_message(
            "eth_getTransactionReceipt", [tx_hash], websocket
        )

        # Retry getting transaction receipt until either it is found or retries are exhausted
        while msg is None and retries > 0:
            await asyncio.sleep(1)
            msg = await self._send_message(
                "eth_getTransactionReceipt", [tx_hash], websocket
            )
            retries -= 1

        match msg:
            case None:
                return msg
            case dict():
                return Receipt.from_dict(msg, infer_missing=True)
            case _:
                return [Receipt.from_dict(result, infer_missing=True) for result in msg]

    async def send_raw_transaction(
        self,
        raw_transaction: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ):
        """
        Returns the receipt of a transaction by transaction hash
        :param raw_transaction: The hash of a transaction
        :param websocket: An optional external websocket for calls to this function
        :type: 32 Byte Hex
        :return: Transaction receipt object
        """
        msg = await self._send_message(
            "eth_sendRawTransaction", [raw_transaction], websocket
        )
        return msg

    async def send_transaction(
        self,
        transaction: dict | list[dict],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ):
        """
        Sends a new method call transaction or contract creation
        """
        return await self._send_message("eth_sendTransaction", [transaction], websocket)

    async def get_protocol_version(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Gets the ethereum protocol version the current node is using
        """
        msg = await self._send_message("eth_protocolVersion", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_sync_status(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool | Sync:
        """
        Returns whether the connected node is syncing to the ethereum network
        """
        msg = await self._send_message("eth_syncing", [], websocket)
        match msg:
            case None:
                return msg
            case bool():
                return msg
            case _:
                return Sync.from_dict(msg, infer_missing=True)

    async def get_coinbase(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> str | HexStr:
        msg = await self._send_message("eth_coinbase", [], websocket)
        return HexStr(msg) if msg is not None else msg

    async def get_chain_id(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Get the chain id to which the current node is connected, will be 1 for main chain ethereum
        """
        msg = await self._send_message("eth_chainId", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def is_mining(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool:
        """
        Gets whether the current node is mining a block, this is now meaningless with proof-of-stake
        """
        return await self._send_message("eth_mining", [], websocket)

    async def get_hashrate(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Gets the rate at which a node is computing hashes for mining, now meaningless with proof-of-stake
        """
        msg = await self._send_message("eth_hashrate", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_accounts(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> list[str | HexStr]:
        """
        Returns a list of addresses owned by client.
        """
        msg = await self._send_message("eth_accounts", [], websocket)
        return [HexStr(result) for result in msg if result is not None]

    async def get_transaction_count_by_hash(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Returns the number of transactions in a block from a block matching the given block hash.
        """
        msg = await self._send_message(
            "eth_getBlockTransactionCountByHash", [data], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_transaction_count_by_number(
        self,
        block_specifier: DefaultBlock | list[DefaultBlock],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Returns the number of transactions in a block matching the given block number.
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getBlockTransactionCountByNumber", [block_specifier], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_uncle_count_by_hash(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Returns the number of uncles in a block from a block matching the given block hash.
        """
        msg = await self._send_message(
            "eth_getUncleCountByBlockHash", [data], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_uncle_count_by_number(
        self,
        block_specifier: DefaultBlock | list[DefaultBlock],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Returns the number of uncles in a block from a block matching the given block number.
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getUncleCountByBlockNumber", [block_specifier], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_code(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        block_specifier: DefaultBlock | list[DefaultBlock],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> str | HexStr | list[str] | list[HexStr]:
        """
        Returns code at a given address for a given block number.
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getCode", [data, block_specifier], websocket
        )
        return msg

    async def sign(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        message: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> str | HexStr | list[str] | list[HexStr]:
        """
        Calculates the ethereum specific signature.

        :param data: 20 byte address(es) to sign with
        :param message: N byte message(s) to be signed
        :param websocket: An optional external websocket for calls to this function
        :return: Hex string(s) containing signature(s) for given data
        """
        msg = await self._send_message("eth_sign", [data, message], websocket)
        match msg:
            case None:
                return msg
            case str():
                return HexStr(msg)
            case list():
                return [HexStr(result) for result in msg]

    async def sign_transaction(
        self,
        tx: TransactionFull | dict | list[TransactionFull] | list[dict],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> HexStr | list[HexStr]:
        """
        Signs a transaction that can be submitted to the network at a later time using with eth_sendRawTransaction.

        :param tx: Transaction object(s) or dict(s) defining transaction parameters to be signed
        :param websocket: An optional external websocket for calls to this function
        :return: Hex string(s) containing result(s) of signed transaction(s)
        """
        msg = await self._send_message("eth_signTransaction", [tx], websocket)
        match msg:
            case None:
                return msg
            case str():
                return HexStr(msg)
            case list():
                return [HexStr(result) for result in msg]

    async def estimate_gas(
        self,
        transaction: dict | list[dict],
        block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Generates and returns an estimate of how much gas is necessary to allow the transaction to complete.
        The transaction will not be added to the blockchain.
        Note that the estimate may be significantly more than the amount of gas actually used by the transaction,
        for a variety of reasons including EVM mechanics and node performance.

        Uses the same parameters as eth_call, see above
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_estimateGas", [transaction, block_specifier], websocket
        )
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def get_transaction_by_hash(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> TransactionFull | list[TransactionFull]:
        """
        Returns the information about a transaction requested by transaction hash.

        :param data: A hash (or list thereof) delineating the transaction(s) to get
        :param websocket: An optional external websocket for calls to this function
        :return: A TransactionFull object (or list thereof) containing information about the selected transaction(s)
        """
        msg = await self._send_message("eth_getTransactionByHash", [data], websocket)
        match msg:
            case None:
                return msg
            case dict():
                return TransactionFull.from_dict(msg, infer_missing=True)
            case _:
                return [
                    TransactionFull.from_dict(result, infer_missing=True)
                    for result in msg
                ]

    async def get_transaction_by_block_hash_and_index(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        index: int | list[int],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> TransactionFull | list[TransactionFull]:
        """
        Returns information about a transaction by block hash and transaction index position.

        :param data: A hash (or list thereof) delineating the block number(s) to get
        :param index: The index position(s) of the transaction(s) for the given block
        :param websocket: An optional external websocket for calls to this function
        :return: A TransactionFull object (or list thereof) containing information about the selected transaction(s)
        """
        msg = await self._send_message(
            "eth_getTransactionByBlockHashAndIndex", [data, index], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return TransactionFull.from_dict(msg, infer_missing=True)
            case _:
                return [
                    TransactionFull.from_dict(result, infer_missing=True)
                    for result in msg
                ]

    async def get_transaction_by_block_number_and_index(
        self,
        block_specifier: DefaultBlock | list[DefaultBlock],
        index: int | list[int],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> TransactionFull | list[TransactionFull]:
        """
        Returns information about a transaction by block number and transaction index position.

        :param block_specifier: A specifier, either int or tag, (or list thereof) delineating the block number(s) to get
        :param index: The index position(s) of the transaction for the given block(s)
        :param websocket: An optional external websocket for calls to this function
        :return: A TransactionFull object (or list thereof) containing information about the selected transaction(s)
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getTransactionByBlockNumberAndIndex",
            [block_specifier, index],
            websocket,
        )
        match msg:
            case None:
                return msg
            case dict():
                return TransactionFull.from_dict(msg, infer_missing=True)
            case _:
                return [
                    TransactionFull.from_dict(result, infer_missing=True)
                    for result in msg
                ]

    async def get_uncle_by_block_hash_and_index(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        index: int | list[int],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Block | list[Block]:
        """
        Returns information about an uncle of a block by hash and uncle index position.

        :param data: A hash delineating the block number to get
        :param index: The index position(s) of the uncle(s) for the given block(s)
        :param websocket: An optional external websocket for calls to this function
        :return: A Block object (or list thereof) containing information about the selected uncle(s)
        """
        msg = await self._send_message(
            "eth_getUncleByBlockHashAndIndex", [data, index], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return Block.from_dict(msg, infer_missing=True)
            case _:
                return [Block.from_dict(result, infer_missing=True) for result in msg]

    async def get_uncle_by_block_number_and_index(
        self,
        block_specifier: DefaultBlock | list[DefaultBlock],
        index: int | list[int],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Block | list[Block]:
        """
        Returns information about an uncle of a block by number and uncle index position.

        :param block_specifier: A specifier, either int or tag, (or list thereof) delineating the block number(s) to get
        :param index: The index position(s) of the uncle(s) for the given block(s)
        :param websocket: An optional external websocket for calls to this function
        :return: A Block object (or list thereof) containing information about the selected uncle(s)
        """
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getUncleByBlockNumberAndIndex", [block_specifier, index], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return Block.from_dict(msg, infer_missing=True)
            case _:
                return [Block.from_dict(result, infer_missing=True) for result in msg]

    async def get_fee_history(
        self,
        block_count: DefaultBlock | list[DefaultBlock],
        newest_block: DefaultBlock | list[DefaultBlock],
        reward_percentiles: list[HexStr]
        | list[int]
        | list[list[HexStr]]
        | list[list[int]] = None,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> FeeHistory | list[FeeHistory]:
        """
        Returns a collection of historical gas information from which you can decide what to submit as your
        maxFeePerGas and/or maxPriorityFeePerGas.

        :param block_count: Number of blocks in the requested range.
            Between 1 and 1024 blocks can be requested in a single query.
            Less than requested may be returned if not all blocks are available.
        :param newest_block: Highest block number of requested range.
        :param reward_percentiles: An optional monotonically increasing list of percentile values to sample
            from each block's effective priority fees per gas in ascending order, weighted by gas used.
        :param websocket: An optional external websocket for calls to this function
        :return: A FeeHistory object (or list thereof) containing information about past fees (at desired percentiles)
        """
        block_count = self._block_formatter(block_count)
        newest_block = self._block_formatter(newest_block)
        if reward_percentiles is None:
            reward_percentiles = []

        msg = await self._send_message(
            "eth_feeHistory", [block_count, newest_block, reward_percentiles], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return FeeHistory.from_dict(msg, infer_missing=True)
            case _:
                return [
                    FeeHistory.from_dict(result, infer_missing=True) for result in msg
                ]

    async def get_proof(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        storage_keys: list[HexStr] | list[str] | list[list[HexStr]] | list[list[str]],
        block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Proof | list[Proof]:
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_getProof",
            [data, storage_keys, block_specifier],
            websocket,
        )
        match msg:
            case None:
                return msg
            case dict():
                return Proof.from_dict(msg, infer_missing=True)
            case _:
                return [Proof.from_dict(result, infer_missing=True) for result in msg]

    async def new_filter(
        self,
        from_block: DefaultBlock | list[DefaultBlock],
        to_block: DefaultBlock | list[DefaultBlock],
        address: str
        | HexStr
        | list[str]
        | list[HexStr]
        | list[list[str]]
        | list[list[HexStr]],
        topics: list[str] | list[HexStr] | list[list[str]] | list[list[HexStr]],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> int | list[int]:
        """
        Creates a filter object based on filter parameters to notify when the state changes.
        To check if the state has changed use EthRPC.get_filter_changes()

        :param from_block: Block from which the filter is active
        :param to_block: Block to which the filter is active
        :param address: Contract address or list of addresses from which logs should originate
        :param topics: Array of 32 byte data topics, topics are order dependent
        :param websocket: An optional external websocket for calls to this function
        :return: Returns an integer filter ID
        """
        param = {
            "from": from_block,
            "to": to_block,
            "address": address,
            "topics": topics,
        }
        msg = await self._send_message("eth_newFilter", [param], websocket)
        match msg:
            case None:
                return msg
            case str():
                return int(msg, 16)
            case _:
                return [
                    int(result, 16) if result is not None else None for result in msg
                ]

    async def new_block_filter(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Creates a filter in the endpoint to notify when a new block arrives.
        To check if the state has changed use EthRPC.get_filter_changes()
        """
        msg = await self._send_message("eth_newBlockFilter", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def new_pending_transaction_filter(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Creates a filter in the endpoint to notify when new pending transactions arrive.
        To check if the state has changed use EthRPC.get_filter_changes()
        """
        msg = await self._send_message("eth_newPendingTransactionFilter", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def uninstall_filter(
        self,
        filter_id: int | str | list[int] | list[str],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> bool | list[bool]:
        """
        Uninstalls a filter with a given name.
        Should always be called when a filter is no longer needed.

        :param filter_id: A filter ID generated by creating a filter previously
        :param websocket: An optional external websocket for calls to this function
        :return: bool or list of bools indicating the success or failure of each filter uninstallation
        """
        filter_id = self._block_formatter(filter_id)
        msg = await self._send_message("eth_uninstallFilter", [filter_id], websocket)
        return msg

    async def get_filter_changes(
        self,
        filter_id: int | str | list[int] | list[str],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> list[HexStr] | list[list[HexStr]]:
        """
        Returns a list of all logs matching filter with given id.
        Used with other filter creation methods taking in their filter numbers as input.

        :param filter_id: A filter ID generated by creating a filter previously
        :param websocket: An optional external websocket for calls to this function
        :return: list of Hex strings (or list of lists) indicating changes made since filter was last checked
        """
        filter_id = self._block_formatter(filter_id)
        msg = await self._send_message("eth_getFilterChanges", [filter_id], websocket)
        match msg:
            case None:
                return msg
            case l if any(isinstance(elem, list) for elem in l):
                return [[HexStr(el) for el in result] for result in msg]
            case list():
                return [HexStr(result) for result in msg]
            case _:
                raise PythereumInvalidReturnException(
                    f"Unexpected return of form {msg} in get_filter_changes"
                )

    async def get_filter_logs(
        self,
        filter_id: int | str | list[int] | list[str],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> list[Log] | list[list[Log]]:
        """
        Returns a list of all logs matching the filter with the provided ID

        :param filter_id: A filter ID generated by creating a filter previously
        :param websocket: An optional external websocket for calls to this function
        :return: list or list of lists of Log objects indicating the new logs created since the filter was last checked
        """
        filter_id = self._block_formatter(filter_id)
        msg = await self._send_message("eth_getFilterLogs", [filter_id], websocket)
        match msg:
            case None:
                return msg
            case l if all(isinstance(elem, list) for elem in l):
                return [[Log.from_dict(el) for el in result] for result in msg]
            case li if isinstance(li, list) and not any(
                isinstance(elem, list) for elem in li
            ):
                return [Log.from_dict(result) for result in msg]
            case _:
                raise PythereumInvalidReturnException(
                    f"Unexpected return of form {msg} in get_filter_changes"
                )

    async def get_logs(
        self,
        from_block: DefaultBlock | list[DefaultBlock],
        to_block: DefaultBlock | list[DefaultBlock],
        address: str
        | HexStr
        | list[str]
        | list[HexStr]
        | list[list[str]]
        | list[list[HexStr]],
        topics: list[str] | list[HexStr] | list[list[str]] | list[list[HexStr]],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> list[Log] | list[list[Log]]:
        """
        :param from_block: Block from which the filter is active
        :param to_block: Block to which the filter is active
        :param address: Contract address or list of addresses from which logs should originate
        :param topics: Array of 32 byte data topics, topics are order dependent
        :param websocket: An optional external websocket for calls to this function
        :return: Returns a list of log objects or nothing if no changes have occurred since last poll
        """
        param = {
            "from": from_block,
            "to": to_block,
            "address": address,
            "topics": topics,
        }
        msg = await self._send_message("eth_getLogs", [param], websocket)
        match msg:
            case None:
                return msg
            case l if all(isinstance(elem, list) for elem in l):
                return [[Log.from_dict(el) for el in result] for result in msg]
            case li if isinstance(li, list) and not any(
                isinstance(elem, list) for elem in li
            ):
                return [Log.from_dict(result) for result in msg]
            case _:
                raise PythereumInvalidReturnException(
                    f"Unexpected return of form {msg} in get_filter_changes"
                )

    # Web3 functions

    async def get_client_version(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> str:
        """
        Returns the current node's client version
        """
        return await self._send_message("web3_clientVersion", [], websocket)

    async def sha3(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> HexStr | list[HexStr]:
        """
        Returns Keccak-256 of the given data

        :param data: A string of data for keccak conversion
        :param websocket: An optional external websocket for calls to this function
        """
        msg = await self._send_message("web3_sha3", [data], websocket)
        match msg:
            case str():
                return HexStr(msg)
            case list():
                return [HexStr(result) for result in msg]
            case _:
                raise PythereumInvalidReturnException(
                    f"Unexpected return of form {msg} in sha3"
                )

    # Net functions

    async def get_net_version(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Returns the network version ID that the current node is connected to
        """
        msg = await self._send_message("net_version", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg)

    async def get_net_listening(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool:
        """
        Returns whether a client is actively listening for network connections
        """
        return await self._send_message("net_listening", [], websocket)

    async def get_net_peer_count(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Returns the number of peers connected to the connected node
        """
        msg = await self._send_message("net_peerCount", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    # OpenEthereum parity functions

    async def get_mempool_parity(
        self,
        tx_limit: int,
        tx_filter: dict,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> TransactionFull | list[TransactionFull]:
        """
        Access the memory pool for a given OpenEthereum parity node, does not work on other node types
        Under testing, feel free to improve.
        """
        msg = await self._send_message(
            "parity_pendingTransactions", [tx_limit, tx_filter], websocket
        )
        match msg:
            case None:
                return msg
            case dict():
                return TransactionFull.from_dict(msg)
            case _:
                return [TransactionFull.from_dict(result) for result in msg]

    # Geth functions

    async def get_mempool_geth(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> MempoolInfo | None:
        """
        Access the memory pool for a geth node, does not work on other node types
        Under testing, feel free to improve.
        Returns a MempoolInfo object to allow users to self select whether they want to include pending txs
        """
        msg = await self._send_message("txpool_content", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                transactions = {"pending": [], "queued": []}

                # Loop through pending and queued transactions, if they exist
                for tx_group in transactions.keys():
                    if tx_group in msg:
                        # iterate through each address that is making transactions
                        for address_data in msg[tx_group].values():
                            # iterate through each tx nonce produced by each address and its associated tx
                            for tx_data in address_data.values():
                                transaction = TransactionFull.from_dict(tx_data)
                                transactions[tx_group].append(transaction)

                return MempoolInfo(transactions["pending"], transactions["queued"])

    # Generic sending

    async def send_raw(
        self,
        method_name: str | HexStr | list[str] | list[HexStr],
        params: list[Any] | list[list[Any]],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Any:
        """
        Sends a custom method name method_name to the endpoint's url with the given parameter list

        :param method_name: A string indicating the method name to be called with the given parameters
        :param params: A list of parameters to be sent for the function call
        :param websocket: An optional external websocket for calls to this function
        :return: Returns the result of the given transaction,
        if the function does not exist for the given params an error will be raised
        """
        return await self._send_message(method_name, params, websocket)
       
        
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
