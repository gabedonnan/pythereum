class BinString:
    """
    Data type representing a binary number
    Implements more intuitive and easily checkable functionality than Python's native string representation
    """
    def __init__(self, bin_string: str | int):
        if isinstance(bin_string, int):
            bin_string = bin(bin_string)
        self.binary = bin_string[2:] if bin_string.startswith(("0b", "0B")) else bin_string
        self.integer_value = int(bin_string, 2)

    def __int__(self) -> int:
        return self.integer_value

    def __str__(self) -> str:
        return self.binary

    def __bytes__(self) -> bytes:
        return bytes(self.binary, "utf-8")

    def __len__(self) -> int:
        return len(self.binary)

    def __repr__(self) -> str:
        return f"BinString(binary={self.binary})"

    def __index__(self):
        return self.__int__()

    def __add__(self, other) -> 'BinString':
        if isinstance(other, BinString):
            return BinString(bin(self.integer_value + other.integer_value))
        elif isinstance(other, int):
            return BinString(bin(self.integer_value + other))
        elif isinstance(other, Hex):
            # You shouldn't really be adding BinString objects directly to Hex but this ensures the program won't break
            return BinString(bin(self.integer_value + other.integer_value))
        elif isinstance(other, str):
            return BinString(bin(self.integer_value + int(other, 2)))


class Hex:
    def __init__(self, hex_string: str | int):
        if isinstance(hex_string, int):
            hex_string = hex(hex_string)
        # Removes the '0x' prefix of an input hex string if it is present
        self.hex_string: str = hex_string[2:] if hex_string.startswith(("0x", "0X")) else hex_string
        self.integer_value: int = int(hex_string, 16)
        self.binary: BinString = BinString(bin(self.integer_value))
        self.base: int = len(self.hex_string)

    def __len__(self):
        return self.base

    def __str__(self):
        return self.hex_string

    def __int__(self):
        return self.integer_value

    def __repr__(self):
        return f"Hex(base={self.base}, string={self.hex_string})"

    def __bytes__(self):
        return bytes(self.hex_string, "utf-8")

    def __index__(self):
        return self.__int__()

    def __eq__(self, other) -> bool:
        if isinstance(other, Hex):
            # Strongly checks equality in case only one of the class values have been adjusted
            return self.hex_string == other.hex_string and self.binary == other.binary and self.base == other.base
        else:
            return False

    def __add__(self, other) -> 'Hex':
        if isinstance(other, Hex):
            return Hex(hex(self.integer_value + other.integer_value))
        elif isinstance(other, int):
            return Hex(hex(self.integer_value + other))
        elif isinstance(other, BinString):
            # You shouldn't really be adding BinString objects directly to Hex but this ensures the program won't break
            return Hex(hex(self.integer_value + other.integer_value))
        elif isinstance(other, str):
            return Hex(hex(self.integer_value + int(other, 16)))
