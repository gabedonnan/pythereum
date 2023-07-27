import json
from dataclasses import dataclass
from enum import Enum

import websockets
from dataclasses_json import dataclass_json, LetterCase
# import eth_utils
from eth_typing import ChecksumAddress
from jsonschema import validate
from typing import List, Any


class BlockTag(str, Enum):
    """ Data type encapsulating all possible non-integer values for a DefaultBlock parameter
    API Documentation at: https://ethereum.org/en/developers/docs/apis/json-rpc/#default-block
    """
    earliest = "earliest"  # Genesis block
    latest = "latest"  # Last mined block
    pending = "pending"  # Pending state/transactions
    safe = "safe"  # Latest safe head block
    finalized = "finalized"  # Latest finalized block


class ERPCRequestException(Exception):
    """
    Raised when an error is returned from the Ethereum RPC
    """

    def __init__(self, code: int, message: str = "Generic ERPC Error"):
        self.code = code
        self.message = message
        super().__init__(f"Error {code}: " + self.message)


class ERPCInvalidReturnException(Exception):
    """
    Raised when the Ethereum RPC returns a value which is incorrectly formatted
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


DefaultBlock = int | BlockTag

Hex64 = str  # 64 bit hex string

Hex20 = str  # 20 bit hex string

HexString = str

RawTransaction = str

HexInt = str  # Hexadecimal representation of an integer number

call_object_schema = {  # A schema for validating call objects
            "type": "object",
            "properties": {
                "from": {"type": "string"},  # Hex20
                "to": {"type": "string"},  # Hex20
                "gas": {"type": "string"},  # int
                "gasPrice": {"type": "string"},  # int
                "value": {"type": "string"},  # int
                "data": {"type": "string"},  # hash
                "chainId": {"type": "string"},  # hex num
                "maxFeePerGas": {"type": "string"},
                "maxPriorityFeePerGas": {"type": "string"}
            },
            "required": ["to"]
        }


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Block:
    difficulty: str
    extra_data: str
    gas_limit: str
    gas_used: str
    hash: str
    logs_bloom: str
    miner: str
    mix_hash: str
    nonce: str
    number: str
    parent_hash: str
    receipts_root: str
    sha3_uncles: str
    size: str
    state_root: str
    timestamp: str
    total_difficulty: str
    transactions: list[str]
    transactions_root: str
    uncles: list[str]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Sync:
    """
    Class representing ethereum sync status
    """
    starting_block: str
    current_block: str
    highest_block: str


def parse_results(res: str | dict) -> Any:
    if isinstance(res, str):
        res = json.loads(res)

    if "result" not in res:
        # Error case as no result is found
        if "error" in res:
            raise ERPCRequestException(res["error"]["code"], res["error"]["message"])
        else:
            raise ERPCInvalidReturnException("Invalid return value from ERPC, check your request.")

    return res["result"]


class EthRPC:
    def __init__(self, url: str) -> None:
        self._url = url
        self._id = 0

    def _next_id(self) -> None:
        self._id += 1

    def build_json(self, method: str, params: list) -> str:
        """
        :param method: ethereum RPC method
        :param params: list of parameters to use in the function call
        :return: json string converted with json.dumps
        This is slightly slower than raw string construction with fstrings, but more elegant
        """
        return json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._id
        })

    async def send_message(self, method: str, params: list[Any]) -> Any:
        async with websockets.connect(self._url) as ws:
            await ws.send(self.build_json(method, params))
            msg = await ws.recv()
        return parse_results(msg)

    async def get_block_number(self) -> int:
        """
        :return: Integer number indicating the number of the most recently mined block
        """
        msg = await self.send_message("eth_blockNumber", [])
        self._next_id()
        return int(msg, 16)

    async def get_transaction_count(self, address: ChecksumAddress, block_specifier: DefaultBlock = BlockTag.latest) -> int:
        """
        Gets the number of transactions sent from a given EOA address
        :param address: The address of an externally owned account
        :param block_specifier: A selector for a block, can be a specifier such as 'latest' or an integer block number
        :return: Integer number of transactions
        """
        msg = await self.send_message("eth_getTransactionCount", [address, block_specifier])
        self._next_id()
        return int(msg, 16)

    async def get_balance(self, contract_address: ChecksumAddress, block_specifier: DefaultBlock = BlockTag.latest) -> int:
        """
        Gets the balance of the account a given address points to
        :param contract_address: Contract address, its balance will be gotten at the block specified by quant_or_tag
        :param block_specifier: A selector for a block, can be a specifier such as 'latest' or an integer block number
        :return: An integer balance in Wei of a given contract
        """
        msg = await self.send_message("eth_getBalance", [contract_address, block_specifier])
        self._next_id()
        return int(msg, 16)

    async def get_gas_price(self) -> int:
        """
        Returns the current price per gas in Wei
        :return: Integer number representing gas price in Wei
        """
        msg = await self.send_message("eth_gasPrice", [])
        self._next_id()
        return int(msg, 16)

    async def get_block_by_number(self, block_specifier: DefaultBlock, full_object: bool = True) -> Block:
        """
        Returns a Block object which represents a block's state
        :param block_specifier: A specifier, either int or tag, delineating the block number to get
        :param full_object: Boolean specifying whether the desired return uses full transactions or transaction hashes
        :return: A Block object representing blocks by either full transactions or transaction hashes
        """
        if isinstance(block_specifier, int):  # Converts integer values from DefaultBlock to hex for parsing
            block_specifier = hex(block_specifier)
        msg = await self.send_message("eth_getBlockByNumber", [block_specifier, full_object])
        self._next_id()
        return Block.from_dict(msg)

    async def get_block_by_hash(self, data: Hex64, full_object: bool = False) -> Block:
        """
        Returns a Block object which represents a block's state
        :param data: Hash of a block
        :param full_object: Boolean specifying whether the desired return uses full transactions or transaction hashes
        :return: A Block object representing blocks by either full transactions or transaction hashes
        """
        msg = await self.send_message("eth_getBlockByHash", [data, full_object])
        self._next_id()
        return Block.from_dict(msg)

    async def call(self, transaction: dict, block_specifier: DefaultBlock = BlockTag.latest):
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
        :return: Hex value of the executed contract
        """
        validate(transaction, call_object_schema)
        msg = await self.send_message("eth_call", [transaction, block_specifier])
        self._next_id()
        return msg

    async def get_transaction_receipt(self, tx_hash: HexString):
        msg = await self.send_message("eth_getTransactionReceipt", [tx_hash])
        self._next_id()
        return msg

    async def send_raw_transaction(self, raw_transaction: RawTransaction):
        """
        Returns the receipt of a transaction by transaction hash
        :param raw_transaction: The hash of a transaction
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
        msg = await self.send_message("eth_sendRawTransaction", [raw_transaction])
        self._next_id()
        return msg

    async def send_transaction(self, transaction: dict):
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
        :return: Transaction hash (or zero hash if the transaction is not yet available)
        :type: 32 Byte Hex
        """
        msg = await self.send_message("eth_sendTransaction", [transaction])
        self._next_id()
        return msg

    async def get_protocol_version(self) -> int:
        msg = await self.send_message("eth_protocolVersion", [])
        self._next_id()
        return int(msg)

    async def get_sync_status(self) -> bool | Sync:
        msg = await self.send_message("eth_syncing", [])
        self._next_id()
        if msg == "false":
            return False
        else:
            return Sync.from_dict(msg)

    async def get_coinbase(self) -> Hex20:
        msg = await self.send_message("eth_coinbase", [])
        self._next_id()
        return msg

    async def get_chain_id(self) -> HexInt:
        msg = await self.send_message("eth_chainId", [])
        self._next_id()
        return msg

    async def is_mining(self) -> bool:
        msg = await self.send_message("eth_mining", [])
        self._next_id()
        return msg

    async def get_hashrate(self) -> int:
        msg = await self.send_message("eth_hashrate", [])
        self._next_id()
        return int(msg, 16)

    async def get_accounts(self) -> List[Hex20]:
        msg = await self.send_message("eth_accounts", [])
        self._next_id()
        return msg