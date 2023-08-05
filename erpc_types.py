class Hex:
    def __init__(self, hex_string: str):
        # Removes the '0x' prefix of an input hex string if it is present
        self.hex_string = hex_string[2:] if hex_string.startswith(("0x", "0X")) else hex_string
        # Converts the hex string to an integer, then to binary and removes the '0b' prefix
        self.binary = bin(int(self.hex_string, 16))[2:]
        self.base = len(self.hex_string)

    def __len__(self):
        return self.base

    def __str__(self):
        return self.hex_string

    def __int__(self):
        return int(self.hex_string, 16)

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
        elif isinstance(other, int):
            return self.__int__() == other
        elif isinstance(other, str):
            # Checks if the compared string is encoded as binary, hexadecimal or neither
            if other.startswith("0b"):
                return f"0b{self.binary}" == other
            elif other.startswith("0B"):
                return f"0B{self.binary}" == other
            elif other.startswith("0x"):
                return f"0x{self.hex_string}" == other
            elif other.startswith("0X"):
                return f"0X{self.hex_string}" == other
            else:
                return self.hex_string == other
        else:
            return False

