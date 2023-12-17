# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import re
from enum import Enum


class GasStrategy(Enum):
    min_price = 0
    max_price = 1
    median_price = 2
    mean_price = 3
    mode_price = 4
    upper_quartile_price = 5
    lower_quartile_price = 6
    custom = 7  # Exists such that custom gas managers may be implemented


class SubscriptionType(str, Enum):
    new_heads = "newHeads"
    logs = "logs"
    new_pending_transactions = "newPendingTransactions"
    syncing = "syncing"


class BlockTag(str, Enum):
    """Data type encapsulating all possible non-integer values for a DefaultBlock parameter
    API Documentation at: https://ethereum.org/en/developers/docs/apis/json-rpc/#default-block
    """

    earliest = "earliest"  # Genesis block
    latest = "latest"  # Last mined block
    pending = "pending"  # Pending state/transactions
    safe = "safe"  # Latest safe head block
    finalized = "finalized"  # Latest finalized block


DefaultBlock = int | BlockTag | str


class EthDenomination(float, Enum):
    """
    An enumeration of all names of eth denominations and their corresponding wei values
    """

    wei = 1.0
    kwei = 1e3
    babbage = 1e3
    femtoether = 1e3
    mwei = 1e6
    lovelace = 1e6
    picoether = 1e6
    gwei = 1e9
    shannon = 1e9
    nanoether = 1e9
    nano = 1e9
    szabo = 1e12
    microether = 1e12
    micro = 1e12
    finney = 1e15
    milliether = 1e15
    milli = 1e15
    ether = 1e18
    eth = 1e18
    kether = 1e21
    grand = 1e21
    mether = 1e24
    gether = 1e27
    tether = 1e30


class HexStr(str):
    """
    Data type representing a base16 hexadecimal number.
    Extends the functionality of the default string type to support hex operations and functionality.

    Attributes:
    - integer_value: returns integer representing the base10 form of the hexadecimal number.
    - raw_hex: returns string representing the hexadecimal number without 0x prefix.
    - hex_bytes: returns bytes object representing the conversion of the value.
    """

    HEX_PATTERN = re.compile(r"^0x[0-9a-fA-F]+$")

    def __new__(cls, value: str | int | bytes):
        if isinstance(value, str):
            formatted_value = cls._format_string_value(value)
        elif isinstance(value, int):
            formatted_value = hex(value)
        elif isinstance(value, bytes):
            formatted_value = cls._format_string_value(value.hex())
        else:
            raise ValueError(
                f"Unsupported type {type(value)} for HexStr. Must be str or int."
            )

        return super().__new__(cls, formatted_value)

    @staticmethod
    def _format_string_value(value: str) -> str:
        """
        Formats a string value to be a proper hex string with a "0x" prefix.
        """
        if HexStr.HEX_PATTERN.match(value):
            return value
        elif not value.startswith(("0x", "0X")):
            value = f"0x{value}"
            if HexStr.HEX_PATTERN.match(value):
                return value

        raise ValueError(f"{value} is not a valid hex string")

    def __int__(self):
        return int(self, 16)

    def __repr__(self) -> str:
        return f"HexStr({super().__repr__()})"

    def __bytes__(self):
        # If odd length, pad with zero to make byte conversion valid
        return bytes.fromhex(self.raw_hex if len(self) % 2 == 0 else f"0{self.raw_hex}")

    @property
    def hex_bytes(self):
        return self.__bytes__()

    @property
    def raw_hex(self):
        return self[2:]

    @property
    def integer_value(self):
        return self.__int__()


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
