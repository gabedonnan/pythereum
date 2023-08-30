import re


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

    def __new__(cls, value: str | int):
        if isinstance(value, str):
            formatted_value = cls._format_string_value(value)
        elif isinstance(value, int):
            formatted_value = hex(value)
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
