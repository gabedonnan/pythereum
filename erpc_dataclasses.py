import re
from typing import Optional
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase, config
from erpc_types import Hex
from erpc_exceptions import (
    ERPCDecoderException, ERPCEncoderException
)


def hex_int_decoder(hex_string: str | None) -> int | None:
    if hex_string is None:
        return None
    elif re.match(r"^(0[xX])?[A-Fa-f0-9]+$", hex_string):
        return int(hex_string, 16)
    else:
        raise ERPCDecoderException(f"{type(hex_string)} \"{hex_string}\" is an invalid input to decoder \"hex_int_decoder\"")


def hex_int_encoder(int_val: int | None) -> str | None:
    if int_val is None:
        return None
    elif not isinstance(int_val, int):
        raise ERPCEncoderException(f"{type(int_val)} {int_val} is an invalid input to encoder \"hex_int_encoder\"")
    return hex(int_val)


def hex_decoder(hex_string: str | None) -> Hex | None:
    if hex_string is None:
        return None
    elif re.match(r"^(0[xX])?[A-Fa-f0-9]+$", hex_string):
        return Hex(hex_string)
    elif hex_string == "0x":
        return None
    else:
        raise ERPCDecoderException(f"{type(hex_string)} \"{hex_string}\" is an invalid input to decoder \"hex_decoder\"")


def hex_encoder(hex_obj: Hex | None) -> str | None:
    """
    Takes in a hex object and returns its hex string representation
    """
    if hex_obj is None:
        return None
    elif not isinstance(hex_obj, Hex):
        raise ERPCEncoderException(f"{type(hex_obj)} {hex_obj} is an invalid input to encoder \"hex_encoder\"")
    return f"0x{hex_obj.hex_string}"


def hex_list_decoder(hex_string_list: list[str] | None) -> list[Hex] | None:
    if hex_string_list is not None:
        return [hex_decoder(hex_string) for hex_string in hex_string_list]
    else:
        return None


def hex_list_encoder(hex_obj_list: list[Hex]) -> list[str] | None:
    if hex_obj_list is not None:
        return [hex_encoder(hex_obj) for hex_obj in hex_obj_list]
    else:
        return None


def transaction_decoder(transaction_hex: dict | str) -> 'Transaction | Hex':
    if isinstance(transaction_hex, dict):
        return Transaction.from_dict(transaction_hex, infer_missing=True)
    else:
        return hex_decoder(transaction_hex)


def transaction_encoder(transaction_obj: 'Hex | Transaction') -> str | dict:
    if isinstance(transaction_obj, Transaction):
        return transaction_obj.to_dict()
    else:
        return hex_encoder(transaction_obj)


def transaction_list_decoder(tr_list: list[dict | str] | None) -> list['Transaction | Hex'] | None:
    if tr_list is not None:
        return [transaction_decoder(transaction) for transaction in tr_list]
    else:
        return None


def transaction_list_encoder(tr_list: list['Transaction| Hex'] | None) -> list[dict | str] | None:
    if tr_list is not None:
        return [transaction_encoder(transaction) for transaction in tr_list]
    else:
        return None


def access_decoder(access_dict: dict | None) -> 'Access | None':
    if access_dict is not None:
        return Access.from_dict(access_dict, infer_missing=True)
    else:
        return None


def access_encoder(access_obj: 'Access | None') -> dict | None:
    if access_obj is not None:
        return access_obj.to_dict()
    else:
        return None


def access_list_decoder(access_list: list[dict] | None) -> list['Access'] | None:
    if access_list is not None:
        return [access_decoder(acc) for acc in access_list]
    else:
        return None


def access_list_encoder(access_obj_list: list['Access'] | None) -> list[dict] | None:
    if access_obj_list is not None:
        return [access_encoder(acc) for acc in access_obj_list]
    else:
        return None


def log_decoder(log_dict: dict | None) -> 'Log | None':
    if log_dict is not None:
        return Log.from_dict(log_dict)
    else:
        return None


def log_encoder(log_obj: 'Log | None') -> dict | None:
    if log_obj is not None:
        return log_obj.to_dict()
    else:
        return None


def log_list_decoder(log_list: list[dict] | None) -> list['Log'] | None:
    if log_list is not None:
        return [log_decoder(lg) for lg in log_list]
    else:
        return None


def log_list_encoder(log_obj_list: list['Log'] | None) -> list[dict] | None:
    if log_obj_list is not None:
        return [log_encoder(lg) for lg in log_obj_list]
    else:
        return None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Block:
    # Integer of the difficulty for the block
    difficulty: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # The extra data field of the block
    extra_data: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # The maximum gas allowed on this block
    gas_limit: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # The total gas used by all transactions in this block
    gas_used: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # 32 Byte hash of a block, null if block is pending
    hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # 256 Bytes bloom filter for the logs of the block. Null if the block is pending
    logs_bloom: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # 20 Byte address of the beneficiary of mining rewards
    miner: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    #
    mix_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # 8 Byte hash of the generated proof of work. Null when the block is pending
    nonce: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # The block number. Null when the block is pending
    number: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # 32 Byte hash of the parent of the block
    parent_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # 32 Byte root of the receipts trie of the block
    receipts_root: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # 32 Byte SHA3 of the uncles of the data in the block
    sha3_uncles: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # Integer size of the block in bytes
    size: int | None = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # 32 Byte root of the final state trie of the block
    state_root: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # The unix timestamp for when the block was collated
    timestamp: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # Integer of the total difficulty of the chain until this block
    total_difficulty: int | None = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # List of all transaction objects or 32 Byte transaction hashes for the block
    transactions: list['Transaction | Hex'] | None = field(
        metadata=config(decoder=transaction_list_decoder, encoder=transaction_list_encoder)
    )

    # 32 Byte root of the transaction trie of the block
    transactions_root: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # List of uncle hashes
    uncles: list[Hex] | None = field(metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Sync:
    """
    Class representing ethereum sync status
    """
    starting_block: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    current_block: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    highest_block: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Receipt:
    # 32 Byte hash of transaction
    transaction_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # Integer of the transactions index position in the block
    transaction_index: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # 32 Byte hash of the block in which the transaction was contained
    block_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # Block number of transaction
    block_number: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # 20 Byte sender address
    from_address: Hex = field(metadata=config(field_name="from", decoder=hex_decoder, encoder=hex_encoder))

    # 20 Byte receiver address, can be null
    to_address: Hex = field(metadata=config(field_name="to", decoder=hex_decoder, encoder=hex_encoder))

    # Total amount of gas used when this transaction was executed on the block
    cumulative_gas_used: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # The sum of the base fee and tip paid per unit gas
    effective_gas_price: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # The amount of gas used by this specific transaction alone
    gas_used: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # The 20 Byte contract address created
    contract_address: Hex | None = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # List of log objects, which this transaction generated
    logs: list['Log'] | None = field(metadata=config(decoder=log_list_decoder, encoder=log_list_encoder))

    # 256 Byte bloom for light clients to quickly retrieve related logs
    logs_bloom: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))

    # Integer representation of transaction type, 0x0 for legacy, 0x1 for list, 0x2 for dynamic fees
    type: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # Optional: 1 (success) or 0 (failure)
    status: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))

    # Optional: 32 Bytes of post-transaction stateroot
    root: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Log:
    address: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    block_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    block_number: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    data: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    log_index: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    topics: list[Hex] = field(metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder))
    transaction_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    transaction_index: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    removed: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Transaction:
    block_hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    block_number: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    from_address: Hex = field(metadata=config(field_name="from", decoder=hex_decoder, encoder=hex_encoder))
    gas: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    gas_price: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    max_fee_per_gas: int | None = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    max_priority_fee_per_gas: int | None = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    hash: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    input: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    nonce: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    to_address: Hex = field(metadata=config(field_name="to", decoder=hex_decoder, encoder=hex_encoder))
    transaction_index: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    value: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    type: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    access_list: list['Access'] | None = field(metadata=config(decoder=access_list_decoder, encoder=access_list_encoder))
    chain_id: int | None = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    v: int = field(metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder))
    r: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    s: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Access:
    """
    Information on access lists available at https://eips.ethereum.org/EIPS/eip-2930
    """
    address: Hex = field(metadata=config(decoder=hex_decoder, encoder=hex_encoder))
    storage_keys: list[Hex] = field(metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder))