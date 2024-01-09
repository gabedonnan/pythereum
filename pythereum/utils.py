from Crypto.Hash import keccak

from pythereum import ERPCGenericException
from pythereum.common import HexStr, EthDenomination
from pythereum.dclasses import TransactionFull
from eth_account._utils.legacy_transactions import (
    encode_transaction,
    serializable_unsigned_transaction_from_dict,
)


def to_checksum_address(address: HexStr | str) -> HexStr:
    """
    Returns the checksummed address given an address
    :param address: The hex address to be checksummed
    :return: The checksummed address
    """
    address = address.lower()
    chars = list(address[2:])

    expanded = bytes([ord(chars[i]) for i in range(40)])

    hashed = keccak.new(digest_bits=256)
    hashed.update(expanded)
    hashed = bytearray(hashed.digest())

    for i in range(0, 40, 2):
        if (hashed[i // 2] >> 4) >= 8:
            chars[i] = chars[i].upper()
        if (hashed[i // 2] & 0x0f) >= 8:
            chars[i + 1] = chars[i + 1].upper()

    return HexStr(''.join(chars))


def recover_raw_transaction(tx: TransactionFull) -> HexStr:
    """
    Recover raw transaction from a TransactionFull object
    :param tx: TransactionFull object to be recovered
    :return: Raw transaction string
    """
    transaction = {
        "chainId": tx.chain_id,
        "nonce": tx.nonce,
        "maxPriorityFeePerGas": tx.max_priority_fee_per_gas,
        "maxFeePerGas": tx.max_fee_per_gas,
        "gas": tx.gas,
        "to": to_checksum_address(tx.to_address),
        "value": tx.value,
        "accessList": tx.access_list,
        "data": tx.input,
    }

    unsigned_transaction = serializable_unsigned_transaction_from_dict(transaction)
    return HexStr(encode_transaction(unsigned_transaction, vrs=(tx.v, tx.r, tx.s)))


def convert_eth(
    quantity: float | str | HexStr,
    convert_from: EthDenomination | str,
    convert_to: EthDenomination | str,
) -> float:
    """
    Converts eth values from a given denomination to another.
    Strings passed in are automatically decoded from hexadecimal to integers, as are Hex values
    """
    if isinstance(quantity, HexStr):
        quantity = quantity.integer_value
    elif isinstance(quantity, str):
        quantity = int(quantity, 16)

    # Allow strings to be used instead of enum values
    if isinstance(convert_from, str):
        if hasattr(EthDenomination, convert_from.lower()):
            convert_from = EthDenomination[convert_from.lower()]
        else:
            raise ERPCGenericException(
                "convert_from value string is not a member of EthDenomination"
            )

    if isinstance(convert_to, str):
        if hasattr(EthDenomination, convert_to.lower()):
            convert_to = EthDenomination[convert_to.lower()]
        else:
            raise ERPCGenericException(
                "convert_to value string is not a member of EthDenomination"
            )

    return (convert_from.value * quantity) / convert_to.value
