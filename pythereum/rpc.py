import json
import statistics
from contextlib import asynccontextmanager

from aiohttp import ClientSession
import websockets
from pythereum.exceptions import (
    ERPCRequestException,
    ERPCInvalidReturnException,
    ERPCSubscriptionException,
    ERPCManagerException
)
from pythereum.common import HexStr, EthDenomination, BlockTag, DefaultBlock, SubscriptionType, GasStrategy
from typing import Any
from pythereum.socket_pool import WebsocketPool
from pythereum.dclasses import Block, Sync, Receipt, Log, Transaction, TransactionFull


def convert_eth(
    quantity: float | str | HexStr,
    convert_from: EthDenomination,
    covert_to: EthDenomination,
) -> float:
    """
    Converts eth values from a given denomination to another.
    Strings passed in are automatically decoded from hexadecimal to integers, as are Hex values
    """
    if isinstance(quantity, str):
        quantity = int(quantity, 16)
    elif isinstance(quantity, HexStr):
        quantity = quantity.integer_value

    return (convert_from.value * quantity) / covert_to.value


def parse_results(res: str | dict, is_subscription: bool = False, builder: str = None) -> Any:
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
            errmsg = res["error"]["message"] + ("" if builder is None else f" for builder {builder}")
            raise ERPCRequestException(res["error"]["code"], errmsg)
        else:
            raise ERPCInvalidReturnException(
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
    ):
        self.subscription_id = subscription_id
        self.socket = socket

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
    def new_pending_transactions_decoder(data: Any) -> HexStr:
        return HexStr(data)

    @staticmethod
    def syncing_decoder(data: Any) -> Sync:
        return Sync.from_dict(data)


class NonceManager:
    """
    Manages the nonces of addresses for the purposes of constructing transactions,
    requires an RPC connection in order to get starting transaction counts for each address.

    Currently operates assuming no other sources are creating transactions from a given address.
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
            raise ERPCManagerException("NonceManager was never given EthRPC or RPC Url instance")
        return self

    async def __aexit__(self, *args):
        if self._close_pool:
            await self.rpc.close_pool()

    async def next_nonce(self, address: str | HexStr) -> int:
        address = HexStr(address)
        if self.rpc is not None and address not in self.nonces:
            self.nonces[address] = await self.rpc.get_transaction_count(address, BlockTag.latest)
        else:
            self.nonces[address] += 1
        return self.nonces[address]

    async def fill_transaction(
        self,
        tx: dict | Transaction | list[dict] | list[Transaction]
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


class GasManager:
    def __init__(
        self,
        rpc: "EthRPC | str | None" = None,
        max_gas_price: float | EthDenomination | None = None,
        max_fee_price: float | EthDenomination | None = None,
        max_priority_price: float | EthDenomination | None = None
    ):
        if isinstance(rpc, str):
            rpc = EthRPC(rpc, 1)
        self.rpc = rpc
        self.latest_transactions = None
        self.max_gas_price = int(max_gas_price if max_gas_price is not None else EthDenomination.tether)
        self.max_fee_price = int(max_fee_price if max_fee_price is not None else EthDenomination.tether)
        self.max_priority_price = int(max_priority_price if max_priority_price is not None else EthDenomination.tether)
        self._close_pool = True

    async def __aenter__(self):
        if self.rpc is not None:
            if not self.rpc.pool_connected():
                await self.rpc.start_pool()
            else:
                self._close_pool = False
        else:
            raise ERPCManagerException("NonceManager was never given EthRPC or RPC Url instance")
        return self

    async def __aexit__(self, *args):
        if self._close_pool:
            await self.rpc.close_pool()

    async def _get_latest_receipts(self, use_stored_results: bool = False) -> list[TransactionFull]:
        """
        Returns a tuple of the latest transaction receipts.
        These are gotten by getting the latest block info and requesting transaction receipts for each transaction.
        To avoid doing this for every call, there is the option to use stored results from the most recent request.
        """
        if use_stored_results:
            transactions = self.latest_transactions
        else:
            latest_block = await self.rpc.get_block_by_number(BlockTag.latest, True)
            transactions = latest_block.transactions
            self.latest_transactions = transactions
        if len(transactions) == 0:
            raise ERPCInvalidReturnException(f"Invalid vlue: {transactions} returned from _get_latest_receipts")
        return transactions

    async def suggest(
        self,
        strategy: GasStrategy,
        attribute: str,
        use_stored_results: bool = False
    ) -> float:
        transactions = await self._get_latest_receipts(use_stored_results)
        prices = [x.__getattribute__(attribute) for x in transactions if x.__getattribute__(attribute) is not None]
        match strategy:
            case GasStrategy.min_price:
                res = min(prices)
            case GasStrategy.max_price:
                res = max(prices)
            case GasStrategy.median_price:
                res = statistics.median(prices)
            case GasStrategy.mean_price:
                res = statistics.mean(prices)
            case GasStrategy.mode_price:
                res = statistics.mode(prices)
            case GasStrategy.upper_quartile_price:
                try:
                    res = statistics.quantiles(prices, n=4)[2]
                except statistics.StatisticsError:
                    res = statistics.mean(prices)
            case GasStrategy.lower_quartile_price:
                try:
                    res = statistics.quantiles(prices, n=4)[0]
                except statistics.StatisticsError:
                    res = statistics.mean(prices)
            case GasStrategy.custom:
                res = self.custom_pricing(prices)
            case _:
                raise ERPCManagerException(f"Invalid strategy of type {strategy} spawned")
        return round(res)

    async def fill_transaction(
        self,
        tx: dict | Transaction | list[dict] | list[Transaction],
        strategy: GasStrategy | dict[str, GasStrategy] = GasStrategy.mean_price,
        use_stored: bool = False
    ) -> None:
        if isinstance(strategy, GasStrategy):  # Allows for separation of strategy types for each type
            strategy = {"gas": strategy, "maxFeePerGas": strategy, "maxPriorityFeePerGas": strategy}

        if isinstance(tx, list):
            for sub_tx in tx:
                sub_tx["gas"] = min(await self.suggest(strategy["gas"], "gas", use_stored), self.max_gas_price)
                sub_tx["maxFeePerGas"] = min(
                    await self.suggest(strategy["maxFeePerGas"], "max_fee_per_gas", True),
                    self.max_fee_price
                )
                sub_tx["maxPriorityFeePerGas"] = min(
                    await self.suggest(strategy["maxPriorityFeePerGas"], "max_priority_fee_per_gas", True),
                    self.max_priority_price
                )
        elif tx is not None:
            tx["gas"] = min(await self.suggest(strategy["gas"], "gas", use_stored), self.max_gas_price)
            tx["maxFeePerGas"] = min(
                await self.suggest(strategy["maxFeePerGas"], "max_fee_per_gas", True),
                self.max_fee_price
            )
            tx["maxPriorityFeePerGas"] = min(
                await self.suggest(strategy["maxPriorityFeePerGas"], "max_priority_fee_per_gas", True),
                self.max_priority_price
            )

    def custom_pricing(self, prices):
        # Override this function when subclassing for custom pricing implementation
        raise ERPCManagerException("Custom pricing strategy not defined for this class")


class EthRPC:
    """
    A class managing communication with an Ethereum node via the Ethereum JSON RPC API.
    """
    def __init__(
        self,
        url: str,
        pool_size: int = 5,
        use_socket_pool: bool = True,
        manage_transaction_nonces: bool = False,
        gas_management_strategy: dict | GasStrategy = None,
        max_gas_price: int | None = None,
        max_fee_price: int | None = None,
        max_priority_price: int | None = None
    ) -> None:
        """
        :param url: URL for the ethereum node to connect to
        :param pool_size: The number of websocket connections opened for the WebsocketPool
        :param use_socket_pool: Whether the socket pool should be used or AIOHTTP requests
        :param manage_transaction_nonces: Boolean determining whether nonces for each transaction will be autofilled,
        one websocket of the pool may be used for autofilling transactions.
        :param gas_management_strategy: A dictionary of GasStrategy objects or single GasStrategy
        :param max_gas_price: The maximum gas price for gas managed transactions
        :param max_fee_price: The maximum gas fee price for managed transactions
        :param max_priority_price: The maximum priority fee for managed transactions
        """
        self._id = 0
        if use_socket_pool:
            self._pool = WebsocketPool(url, pool_size)
        else:
            self._pool = None
            self.session = ClientSession()
        self._http_url = url.replace("wss://", "https://").replace("ws://", "http://")
        self.manage_transaction_nonces = manage_transaction_nonces
        self.gas_management_strategy = gas_management_strategy
        self.nonce_manager = NonceManager()
        self.gas_manager = GasManager(
            max_gas_price=max_gas_price,
            max_fee_price=max_fee_price,
            max_priority_price=max_priority_price
        )

    def _next_id(self) -> None:
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
        if all(isinstance(param, list) for param in (from_block, to_block, address, topics)):
            # Detects whether a set of filter options is batched
            return [
                {
                    "fromBlock": f,
                    "toBlock": t,
                    "address": a,
                    "topics": tpc
                } for (f, t, a, tpc) in zip(from_block, to_block, address, topics)
            ]
        else:
            # Non-batched object return
            return {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": address,
                "topics": topics
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
        if isinstance(
            block_specifier, int
        ):  # Converts integer values from DefaultBlock to hex for parsing
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
            return [item for item in zip(*param_list)]
        else:
            return param_list

    def pool_connected(self) -> bool:
        if self._pool is None:
            return False
        else:
            return self._pool.connected

    async def start_pool(self) -> None:
        """Exposes the ability to start the ERPC's socket pool before the first method call"""
        if self._pool is not None:
            await self._pool.start()
        else:
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
        json_builder = (
            self._build_batch_json
            if any(isinstance(param, tuple) for param in params)
            else self._build_json
        )
        built_msg = json_builder(method, params)
        if websocket is None:
            # Gets a new websocket if one is not supplied to the function
            if self._pool is not None:
                # Using websocket pool
                async with self._pool.get_socket() as ws:
                    await ws.send(built_msg)
                    msg = await ws.recv()
            else:
                # Creating new websocket connections
                async with self.session.post(
                        url=self._http_url,
                        data=built_msg,
                        headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status != 200:
                        raise ERPCRequestException(
                            resp.status,
                            f"Invalid EthRPC aiohttp request for url {self._http_url} of form {built_msg}"
                        )

                    msg = await resp.json()
        else:
            # Using a given websocket
            await websocket.send(built_msg)
            msg = await websocket.recv()
        return parse_results(msg, is_subscription)

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
                    subscription_id=subscription_id, socket=ws, subscription_type=method
                )
                yield sub
            finally:
                if subscription_id == "":
                    raise ERPCSubscriptionException(
                        f"Subscription of type {method.value} rejected by destination."
                    )
                await self.unsubscribe(subscription_id, ws)

    # Public RPC methods

    async def get_subscription(
        self,
        method: SubscriptionType,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> str:
        """
        Supporting function for self.subscribe, opening a subscription for the provided websocket
        """
        return await self._send_message("eth_subscribe", [method.value], websocket)

    async def unsubscribe(
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
        cannot be batched
        :return: Integer number indicating the number of the most recently mined block
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
        Cannot be batched
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
        transaction: dict | list[dict],
        block_specifier: DefaultBlock | list[DefaultBlock] = BlockTag.latest,
        websocket: websockets.WebSocketClientProtocol | None = None,
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
        block_specifier = self._block_formatter(block_specifier)
        msg = await self._send_message(
            "eth_call", [transaction, block_specifier], websocket
        )
        return msg

    async def get_transaction_receipt(
        self,
        tx_hash: str | HexStr | list[str] | list[HexStr],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Receipt | list[Receipt]:
        """
        Gets the receipt of a transaction given its hash, the definition of a receipt can be seen in dclasses.py
        """
        msg = await self._send_message(
            "eth_getTransactionReceipt", [tx_hash], websocket
        )
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
        strategy: dict | GasStrategy = GasStrategy.mean_price,
        websocket: websockets.WebSocketClientProtocol | None = None,
    ):
        """
        Creates a new message call transaction or contract creation
        """
        if self.manage_transaction_nonces:
            if transaction["from"] not in self.nonce_manager.nonces:
                # 1 must be subtracted from the current transaction count as it will be incremented for fill_transaction
                self.nonce_manager["from"] = await self.get_transaction_count(transaction["from"], BlockTag.latest) - 1
            await self.nonce_manager.fill_transaction(transaction)
        if self.gas_management_strategy is not None:
            self.gas_manager.latest_transactions = (await self.get_block_by_number(BlockTag.latest, True)).transactions
            await self.gas_manager.fill_transaction(transaction, strategy, True)
        return await self._send_message("eth_sendTransaction", [transaction], websocket)

    async def get_protocol_version(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        msg = await self._send_message("eth_protocolVersion", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def get_sync_status(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool | Sync:
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
        msg = await self._send_message("eth_chainId", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

    async def is_mining(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool:
        return await self._send_message("eth_mining", [], websocket)

    async def get_hashrate(
        self, websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
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
            websocket: websockets.WebSocketClientProtocol | None = None
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
                    TransactionFull.from_dict(result, infer_missing=True) for result in msg
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
                    TransactionFull.from_dict(result, infer_missing=True) for result in msg
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
                    TransactionFull.from_dict(result, infer_missing=True) for result in msg
                ]

    async def get_uncle_by_block_hash_and_index(
        self,
        data: str | HexStr | list[str] | list[HexStr],
        index: int | list[int],
        websocket: websockets.WebSocketClientProtocol | None = None,
    ) -> Block | list[Block]:
        """
        Returns information about a uncle of a block by hash and uncle index position.

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
        Returns information about a uncle of a block by number and uncle index position.

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
        param = {"from": from_block, "to": to_block, "address": address, "topics": topics}
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
                raise ERPCInvalidReturnException(
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
                raise ERPCInvalidReturnException(
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
        param = {"from": from_block, "to": to_block, "address": address, "topics": topics}
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
                raise ERPCInvalidReturnException(
                    f"Unexpected return of form {msg} in get_filter_changes"
                )

    # Web3 functions

    async def get_client_version(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> str:
        """
        Returns the current client version
        """
        return await self._send_message("web3_clientVersion", [], websocket)

    async def sha3(
            self,
            data: str | HexStr | list[str] | list[HexStr],
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> HexStr | list[HexStr]:
        """
        Returns Keccac-256 of the given data

        :param data: A string of data for keccac conversion
        :param websocket: An optional external websocket for calls to this function
        """
        msg = await self._send_message("web3_sha3", [data], websocket)
        match msg:
            case str():
                return HexStr(msg)
            case list():
                return [HexStr(result) for result in msg]
            case _:
                raise ERPCInvalidReturnException(f"Unexpected return of form {msg} in sha3")

    # Net functions

    async def get_net_version(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Returns the network version ID
        """
        msg = await self._send_message("net_version", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg)

    async def get_net_listening(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> bool:
        """
        Returns whether a client is actively listening for network connections
        """
        return await self._send_message("net_listening", [], websocket)

    async def get_net_peer_count(
            self,
            websocket: websockets.WebSocketClientProtocol | None = None
    ) -> int:
        """
        Returns the number of peers connected to the client
        """
        msg = await self._send_message("net_peerCount", [], websocket)
        match msg:
            case None:
                return msg
            case _:
                return int(msg, 16)

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
