from Crypto.Hash import keccak
from pythereum.common import HexStr
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

    expanded = bytearray(40)
    for i in range(40):
        expanded[i] = ord(chars[i])

    hashed = keccak.new(digest_bits=256)
    hashed.update(bytes(expanded))
    hashed = bytearray(hashed.digest())


    for i in range(0, 40, 2):
        if (hashed[i // 2] >> 4) >= 8:
            chars[i] = chars[i].upper()
        if (hashed[i // 2] & 0x0f) >= 8:
            chars[i + 1] = chars[i + 1].upper()

    return "0x" + ''.join(chars)


def recover_raw_transaction(tx: TransactionFull) -> str:
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

    v = tx.v
    r = tx.r
    s = tx.s
    unsigned_transaction = serializable_unsigned_transaction_from_dict(transaction)
    return "0x" + encode_transaction(unsigned_transaction, vrs=(v, r, s)).hex()