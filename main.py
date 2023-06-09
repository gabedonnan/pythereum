from enum import Enum
from jsonschema import validate, ValidationError, SchemaError
import requests
import eth_utils
from eth_typing import ChecksumAddress


class BlockTag(str, Enum):
    """ Data type encapsulating all possible non-integer values for a DefaultBlock parameter
    API Documentation at: https://ethereum.org/en/developers/docs/apis/json-rpc/#default-block
    """
    earliest = "earliest"  # Genesis block
    latest = "latest"  # Last mined block
    pending = "pending"  # Pending state/transactions
    safe = "safe"  # Latest safe head block
    finalized = "finalized"  # Latest finalized block


DefaultBlock = int | BlockTag

Hex64 = str  # 64 bit hex string

Hex20 = str  # 20 bit hex string

HexString = str

RawTransaction = str

call_object_schema = {  # A schema for validating call objects
            "type": "object",
            "properties" : {
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

class EthereumRPC:
    def __init__(self, url: str) -> None:
        """
        :param url: URL to connect to, currently does not work with wss://, must convert to https://
        """
        self._url = url
        self._id = 0

    def get_block_number(self) -> int:
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": self._id
            }
        ).json()
        self._next_id()
        try:
            return int(res["result"], 16)
        except KeyError as ke:
            print(f"KEY ERROR: {ke}")
            print(f"REQUEST RESULT: {res}")
        except ValueError as ve:
            print(f"VALUE ERROR: {ve}")
            print(f"REQUEST RESULT: {res}")
        return -1

    def get_transaction_count(self, eoa_address: ChecksumAddress, quant_or_tag: DefaultBlock = BlockTag.latest) -> int:
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_getTransactionCount",
                "params": [eoa_address, quant_or_tag],
                "id": self._id
            }
        ).json()
        self._next_id()
        try:
            return int(res["result"], 16)
        except KeyError as ke:
            print(f"KEY ERROR: {ke}")
            print(f"REQUEST RESULT: {res}")
        except ValueError as ve:
            print(f"VALUE ERROR: {ve}")
            print(f"REQUEST RESULT: {res}")
        return -1

    def get_balance(self, contract_address: ChecksumAddress, quant_or_tag: DefaultBlock = BlockTag.latest) -> int:
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [contract_address, quant_or_tag],
                "id": self._id
            }
        ).json()
        self._next_id()
        try:
            return int(res["result"], 16)
        except KeyError as ke:
            print(f"KEY ERROR: {ke}")
            print(f"REQUEST RESULT: {res}")
        except ValueError as ve:
            print(f"VALUE ERROR: {ve}")
            print(f"REQUEST RESULT: {res}")
        return -1

    def get_gas_price(self) -> int:
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_gasPrice",
                "params": [],
                "id": self._id
            }
        ).json()
        self._next_id()
        try:
            return int(res["result"], 16)
        except KeyError as ke:
            print(f"KEY ERROR: {ke}")
            print(f"REQUEST RESULT: {res}")
        except ValueError as ve:
            print(f"VALUE ERROR: {ve}")
            print(f"REQUEST RESULT: {res}")
        return -1

    def get_block_by_number(self, block: DefaultBlock, full_object: bool = True):
        if isinstance(block, int):  # Converts integer values from DefaultBlock to hex for parsing
            block = hex(block)
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBlockByNumber",
                "params": [block, full_object],
                "id": self._id
            }
        ).json()  # Use dataclasses json to parse objects
        self._next_id()
        return res["result"]

    def get_block_by_hash(self, data: Hex64, full_object: bool = True) -> dict:
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBlockByHash",
                "params": [data, full_object],
                "id": self._id
            }
        ).json()
        self._next_id()
        return res["result"]

    def call(self, transaction: dict, block: DefaultBlock = BlockTag.latest):
        try:
            validate(transaction, call_object_schema)
        except SchemaError:
            print(f"There is an error with the schema 'call_object_schema'")
        except ValidationError as e:
            print(e)
            print("---------")
            print(e.absolute_path)

            print("---------")
            print(e.absolute_schema_path)
            return "0x"  # Empty, maybe change this to be more informative later

        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [transaction, block],
                "id": self._id
            }
        ).json()  # Use dataclasses json to parse objects
        self._next_id()
        return res["result"]

    def get_transaction_receipt(self, tx_hash: HexString):
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_getTransactionReceipt",
                "params": [tx_hash],
                "id": self._id
            }
        ).json()
        self._next_id()
        return res["result"]

    def send_raw_transaction(self, raw_transaction: RawTransaction):
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_sendRawTransaction",
                "params": [raw_transaction],
                "id": self._id
            }
        ).json()
        self._next_id()
        print(res)
        return res["result"]

    def send_transaction(self, transaction: dict):
        res = requests.post(
            self._url,
            json={
                "jsonrpc": "2.0",
                "method": "eth_sendTransaction",
                "params": [transaction],
                "id": self._id
            }
        ).json()
        self._next_id()

        return res["result"]

    def _next_id(self) -> int:
        self._id += 1
        return self._id
