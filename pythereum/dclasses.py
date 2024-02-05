# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

# Yes all these decoders are stupid, they will need refactoring soon.

import re
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase, config
from pythereum.common import HexStr
from pythereum.exceptions import PythereumDecoderException, PythereumEncoderException


def hex_int_decoder(hex_string: str | None) -> int | None:
    if hex_string is None:
        return None
    elif re.match(r"^(0[xX])?[A-Fa-f0-9]+$", hex_string):
        return int(hex_string, 16)
    else:
        raise PythereumDecoderException(
            f'{type(hex_string)} "{hex_string}" is an invalid input to decoder "hex_int_decoder"'
        )


def hex_int_encoder(int_val: int | None) -> str | None:
    if int_val is None:
        return None
    elif not isinstance(int_val, int):
        raise PythereumEncoderException(
            f'{type(int_val)} {int_val} is an invalid input to encoder "hex_int_encoder"'
        )
    return hex(int_val)


def hex_decoder(hex_string: str | None) -> HexStr | None:
    if hex_string is None:
        return None
    elif re.match(r"^(0[xX])?[A-Fa-f0-9]+$", hex_string):
        return HexStr(hex_string)
    elif hex_string == "0x":
        return None
    else:
        raise PythereumDecoderException(
            f'{type(hex_string)} "{hex_string}" is an invalid input to decoder "hex_decoder"'
        )


def hex_encoder(hex_obj: HexStr | None) -> str | None:
    """
    Takes in a hex object and returns its hex string representation
    """
    if hex_obj is None:
        return None
    elif not isinstance(hex_obj, HexStr):
        raise PythereumEncoderException(
            f'{type(hex_obj)} {hex_obj} is an invalid input to encoder "hex_encoder"'
        )
    return str(hex_obj)


def hex_list_decoder(hex_string_list: list[str] | None) -> list[HexStr] | None:
    if hex_string_list is not None:
        return [hex_decoder(hex_string) for hex_string in hex_string_list]
    return None


def hex_list_encoder(hex_obj_list: list[HexStr] | None) -> list[str] | None:
    if hex_obj_list is not None:
        return [hex_encoder(hex_obj) for hex_obj in hex_obj_list]
    return None


def hex_list_list_decoder(
    hex_string_list: list[list[str]] | None,
) -> list[list[HexStr]] | None:
    if hex_string_list is not None:
        return [hex_list_decoder(hex_string) for hex_string in hex_string_list]
    return None


def hex_list_list_encoder(
    hex_obj_list: list[list[HexStr]] | None,
) -> list[list[str]] | None:
    if hex_obj_list is not None:
        return [hex_list_encoder(hex_obj) for hex_obj in hex_obj_list]
    return None


def transaction_decoder(
    transaction_hex: dict | str | None,
) -> "TransactionFull | HexStr | None":
    if isinstance(transaction_hex, dict):
        return TransactionFull.from_dict(transaction_hex, infer_missing=True)
    elif transaction_hex is not None:
        return hex_decoder(transaction_hex)
    return None


def transaction_encoder(
    transaction_obj: "HexStr | TransactionFull | None",
) -> str | dict | None:
    if isinstance(transaction_obj, TransactionFull):
        return transaction_obj.to_dict()
    elif transaction_obj is not None:
        return hex_encoder(transaction_obj)
    return None


def transaction_list_decoder(
    tr_list: list[dict | str] | None,
) -> list["TransactionFull | HexStr"] | None:
    if tr_list is not None:
        return [transaction_decoder(transaction) for transaction in tr_list]
    return None


def transaction_list_encoder(
    tr_list: list["TransactionFull | HexStr"] | None,
) -> list[dict | str] | None:
    if tr_list is not None:
        return [transaction_encoder(transaction) for transaction in tr_list]
    return None


def access_decoder(access_dict: dict | None) -> "Access | None":
    if access_dict is not None:
        return Access.from_dict(access_dict, infer_missing=True)
    return None


def access_encoder(access_obj: "Access | None") -> dict | None:
    if access_obj is not None:
        return access_obj.to_dict()
    return None


def access_list_decoder(access_list: list[dict] | None) -> list["Access"] | None:
    if access_list is not None:
        return [access_decoder(acc) for acc in access_list]
    return None


def access_list_encoder(access_obj_list: list["Access"] | None) -> list[dict] | None:
    if access_obj_list is not None:
        return [access_encoder(acc) for acc in access_obj_list]
    return None


def storage_proof_decoder(storage_proof: dict | None) -> "StorageProof | None":
    if storage_proof is not None:
        return StorageProof.from_dict(storage_proof)
    return None


def storage_proof_encoder(storage_proof: "StorageProof | None") -> dict | None:
    if storage_proof is not None:
        return storage_proof.to_dict()
    return None


def storage_proof_list_decoder(
    storage_proof_list: list[dict] | None,
) -> list["StorageProof"] | None:
    if storage_proof_list is not None:
        return [
            storage_proof_decoder(storage_proof) for storage_proof in storage_proof_list
        ]
    return None


def storage_proof_list_encoder(
    storage_proof_list: list["StorageProof"] | None,
) -> list[dict] | None:
    if storage_proof_list is not None:
        return [
            storage_proof_encoder(storage_proof) for storage_proof in storage_proof_list
        ]
    return None


def log_decoder(log_dict: dict | None) -> "Log | None":
    if log_dict is not None:
        return Log.from_dict(log_dict)
    return None


def log_encoder(log_obj: "Log | None") -> dict | None:
    if log_obj is not None:
        return log_obj.to_dict()
    return None


def log_list_decoder(log_list: list[dict] | None) -> list["Log"] | None:
    if log_list is not None:
        return [log_decoder(lg) for lg in log_list]
    return None


def log_list_encoder(log_obj_list: list["Log"] | None) -> list[dict] | None:
    if log_obj_list is not None:
        return [log_encoder(lg) for lg in log_obj_list]
    return None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Block:
    """
    Full information about a block, either including full transactions or transaction hashes
    """

    # Integer of the difficulty for the block
    difficulty: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # The extra data field of the block
    extra_data: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # The maximum gas allowed on this block
    gas_limit: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # The total gas used by all transactions in this block
    gas_used: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # 32 Byte hash of a block, null if block is pending
    hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # 256 Bytes bloom filter for the logs of the block. Null if the block is pending
    logs_bloom: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # 20 Byte address of the beneficiary of mining rewards
    miner: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    #
    mix_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # 8 Byte hash of the generated proof of work. Null when the block is pending
    nonce: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # The block number. Null when the block is pending
    number: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # 32 Byte hash of the parent of the block
    parent_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # 32 Byte root of the receipts trie of the block
    receipts_root: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # 32 Byte SHA3 of the uncles of the data in the block
    sha3_uncles: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # Integer size of the block in bytes
    size: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # 32 Byte root of the final state trie of the block
    state_root: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # The unix timestamp for when the block was collated
    timestamp: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # Integer of the total difficulty of the chain until this block
    total_difficulty: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # List of all transaction objects or 32 Byte transaction hashes for the block
    transactions: list["TransactionFull | HexStr"] | None = field(
        metadata=config(
            decoder=transaction_list_decoder, encoder=transaction_list_encoder
        )
    )

    # 32 Byte root of the transaction trie of the block
    transactions_root: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # List of uncle hashes
    uncles: list[HexStr] | None = field(
        metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder)
    )

    # The base fee per gas, only added after EIP-1559
    base_fee_per_gas: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Sync:
    """
    Class representing ethereum sync status
    """

    starting_block: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    current_block: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    highest_block: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Receipt:
    """
    A receipt generated by a transaction's execution
    """

    # 32 Byte hash of transaction
    transaction_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # Integer of the transactions index position in the block
    transaction_index: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # 32 Byte hash of the block in which the transaction was contained
    block_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # Block number of transaction
    block_number: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # 20 Byte sender address
    from_address: HexStr | None = field(
        metadata=config(field_name="from", decoder=hex_decoder, encoder=hex_encoder)
    )

    # 20 Byte receiver address, can be null
    to_address: HexStr | None = field(
        metadata=config(field_name="to", decoder=hex_decoder, encoder=hex_encoder)
    )

    # Total amount of gas used when this transaction was executed on the block
    cumulative_gas_used: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # The sum of the base fee and tip paid per unit gas
    effective_gas_price: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # The amount of gas used by this specific transaction alone
    gas_used: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # The 20 Byte contract address created
    contract_address: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # List of log objects, which this transaction generated
    logs: list["Log"] | None = field(
        metadata=config(decoder=log_list_decoder, encoder=log_list_encoder)
    )

    # 256 Byte bloom for light clients to quickly retrieve related logs
    logs_bloom: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

    # Integer representation of transaction type, 0x0 for legacy, 0x1 for list, 0x2 for dynamic fees
    type: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # Optional: 1 (success) or 0 (failure)
    status: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )

    # Optional: 32 Bytes of post-transaction stateroot
    root: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Log:
    """
    A log generated by smart contract event triggers
    """

    address: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    block_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    block_number: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    data: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    log_index: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    topics: list[HexStr] | None = field(
        metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder)
    )
    transaction_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    transaction_index: int | None = field(
        metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    removed: bool | None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TransactionFull:
    """
    The full information on a transaction to be executed, including metadata with reference to its inclusion on chain
    """

    block_hash: HexStr | None = field(
        default=None, metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    block_number: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    from_address: HexStr | None = field(
        default=None,
        metadata=config(field_name="from", decoder=hex_decoder, encoder=hex_encoder),
    )
    gas: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    gas_price: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    max_fee_per_gas: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    max_priority_fee_per_gas: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    hash: HexStr | None = field(
        default=None, metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    input: HexStr | None = field(
        default=None, metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    nonce: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    to_address: HexStr | None = field(
        default=None,
        metadata=config(field_name="to", decoder=hex_decoder, encoder=hex_encoder),
    )
    transaction_index: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    value: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    type: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    access_list: list["Access"] | None = field(
        metadata=config(decoder=access_list_decoder, encoder=access_list_encoder),
        default_factory=list,
    )
    chain_id: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    v: int | None = field(
        default=None, metadata=config(decoder=hex_int_decoder, encoder=hex_int_encoder)
    )
    r: HexStr | None = field(
        default=None, metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    s: HexStr | None = field(
        default=None, metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Access:
    """
    Information on access lists available at https://eips.ethereum.org/EIPS/eip-2930
    """

    address: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    storage_keys: list[HexStr] | None = field(
        metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder)
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class FeeHistory:
    oldest_block: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    base_fee_per_gas: list[HexStr] | None = field(
        metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder)
    )
    gas_used_ratio: list[float] | None
    reward: list[list[HexStr]] | None = field(
        metadata=config(decoder=hex_list_list_decoder, encoder=hex_list_list_encoder)
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class StorageProof:
    key: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    value: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    proof: list[HexStr] | None = field(
        metadata=config(decoder=hex_list_decoder, encoder=hex_list_encoder)
    )


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Proof:
    balance: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    code_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    nonce: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    storage_hash: HexStr | None = field(
        metadata=config(decoder=hex_decoder, encoder=hex_encoder)
    )
    storage_proof: list[StorageProof] | None = field(
        metadata=config(
            decoder=storage_proof_list_decoder, encoder=storage_proof_list_encoder
        )
    )


@dataclass
class MempoolInfo:
    pending: list[TransactionFull]
    queued: list[TransactionFull]


class Transaction(dict):
    """
    from_address: Address from which fees should be sent. Transaction must be signed by private key from this account.

    to_address: Address to which fees are sent

    max_priority_fee_per_gas: The maximum price of the consumed gas to be included as a tip to the validator

    max_fee_per_gas: The maximum fee per unit of gas willing to be paid for the transaction
    (inclusive of baseFeePerGas and maxPriorityFeePerGas)

    gas: Maximum gas allocated for execution of the transaction onchain (evm specifies the correct amount to use)

    value: Value in wei sent from the from_address to to_address

    data: Optional extra data

    nonce: A sequentially incrementing counter uniquely identifying each transaction from each account
    """

    def __init__(
        self,
        from_address: str | HexStr,
        to_address: str | HexStr | None = None,
        max_priority_fee_per_gas: int | HexStr | str | None = None,
        max_fee_per_gas: int | HexStr | str | None = None,
        gas: int | HexStr | str | None = None,
        value: int | HexStr | str | None = None,
        data: str | HexStr | None = None,
        nonce: int | HexStr | str | None = None,
        chain_id: int | HexStr | str | None = None,
    ):
        if from_address is not None:
            from_address = HexStr(from_address)

        if to_address is not None:
            to_address = HexStr(to_address)

        if data is not None:
            data = HexStr(data)

        if isinstance(max_priority_fee_per_gas, int):
            max_priority_fee_per_gas = HexStr(max_priority_fee_per_gas)

        if isinstance(max_fee_per_gas, int):
            max_fee_per_gas = HexStr(max_fee_per_gas)

        if isinstance(gas, int):
            gas = HexStr(gas)

        if isinstance(value, int):
            value = HexStr(value)

        if isinstance(nonce, int):
            nonce = HexStr(nonce)

        if isinstance(chain_id, int):
            chain_id = HexStr(chain_id)

        super().__init__(
            {
                key: val
                for key, val in zip(
                    (
                        "from",
                        "to",
                        "maxPriorityFeePerGas",
                        "maxFeePerGas",
                        "gas",
                        "value",
                        "data",
                        "nonce",
                        "chainId",
                    ),
                    (
                        from_address,
                        to_address,
                        max_priority_fee_per_gas,
                        max_fee_per_gas,
                        gas,
                        value,
                        data,
                        nonce,
                        chain_id,
                    ),
                )
                if val is not None
            }
        )


class Bundle(dict):
    """
    A bundle of transactions to submit to a block builder
    """

    def __init__(
        self,
        txs: list[str] | list[HexStr],
        block_number: str | HexStr | None = None,
        min_timestamp: int | HexStr | str | None = None,
        max_timestamp: int | HexStr | str | None = None,
        reverting_tx_hashes: list[str] | list[HexStr] | None = None,
        uuid: str | HexStr | None = None,
        replacement_uuid: str | HexStr | None = None,
        refund_percent: int | HexStr | str | None = None,
        refund_index: int | HexStr | str | None = None,
        refund_recipient: str | HexStr | None = None,
        refund_tx_hashes: list[str] | list[HexStr] | None = None,
    ):
        res = {"txs": txs}

        if block_number is not None:
            res["blockNumber"] = block_number

        if min_timestamp is not None:
            res["minTimestamp"] = min_timestamp

        if max_timestamp is not None:
            res["maxTimestamp"] = max_timestamp

        if reverting_tx_hashes is not None:
            res["revertingTxHashes"] = reverting_tx_hashes

        if uuid is not None:
            res["uuid"] = uuid

        if replacement_uuid is not None:
            res["replacementUuid"] = replacement_uuid

        if refund_percent is not None:
            res["refundPercent"] = refund_percent

        if refund_index is not None:
            res["refundIndex"] = refund_index

        if refund_recipient is not None:
            res["refundRecipient"] = refund_recipient

        if refund_tx_hashes is not None:
            res["refundTxHashes"] = refund_tx_hashes

        super().__init__(res)


class MEVBundle(dict):
    def __init__(
        self,
        version: str = "v0.1",
        block: HexStr | int | str = 0,
        max_block: HexStr | int | str | None = None,
        flashbots_hashes: list[HexStr] | list[str] | None = None,
        transactions: list[HexStr] | list[str] | None = None,
        transactions_can_revert: bool | list[bool] = False,
        extra_mev_bundles: list[dict] | None = None,
        refund_addresses: list[str] | None = None,
        refund_percentages: list[int] | None = None,
        valid_builders: list[str] | None = None,
    ):
        """
        :param version: (OPTIONAL) MEVBoost protocol version to use
        :param block: The first (or only) block in which this bundle must be included
        :param max_block: (OPTIONAL) The maximum block height in which this bundle may be included
        :param flashbots_hashes: (OPTIONAL) The hashes of flashbots transactions (transactions returned by flashbots)
        :param transactions: (OPTIONAL) The hex hashes of signed transactions to be passed
        :param transactions_can_revert: (OPTIONAL) Bool or list of bools defining whether each transaction may be reverted
        :param extra_mev_bundles: (OPTIONAL) MEV bundles may be compounded, this parameter is a list of extra MEV bundles to include in this bundle
        :param refund_addresses: A list of addresses for refunds to be addressed to
        :param refund_percentages: A list of integers defining the percentage of refunds directed to each address
        :param valid_builders: A list of builders who are allowed to execute this MEV bundle
        """
        if not isinstance(block, HexStr):
            block = HexStr(block)

        if max_block is not None and not isinstance(max_block, HexStr):
            max_block = HexStr(max_block)

        if refund_percentages is None:
            refund_percentages = [100]

        if isinstance(transactions_can_revert, bool):
            transactions_can_revert = [
                transactions_can_revert for _ in range(len(transactions))
            ]

        res = {"version": version, "inclusion": {"block": block}, "body": []}
        if flashbots_hashes is not None:
            res["body"].extend([{"hash": f_hash} for f_hash in flashbots_hashes])

        if transactions is not None:
            res["body"].extend(
                [
                    {"tx": tx, "canRevert": rvt}
                    for tx, rvt in zip(transactions, transactions_can_revert)
                ]
            )

        if extra_mev_bundles is not None:
            res["body"].extend([{"bundle": bd} for bd in extra_mev_bundles])

        if max_block is not None:
            res["inclusion"]["maxBlock"] = max_block

        if refund_addresses is not None:
            res["validity"] = {
                "refundConfig": [
                    {"address": r_address, "percent": r_percent}
                    for r_address, r_percent in zip(
                        refund_addresses, refund_percentages
                    )
                ]
            }

        if valid_builders is not None:
            res["privacy"] = {"builders": valid_builders}

        super().__init__(res)


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
