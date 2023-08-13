class Binary:
    """
    Data type representing a base2 binary number.
    Implements more intuitive and easily checkable functionality than Python's native string representation

    self.binary : Contains a string representation of a binary number

    self.integer_value : Contains a base10 integer representation of the stored binary number

    self.raw_binary : Contains a string representation of a binary number without 0b prefix
    """

    def __init__(self, bin_string: str | int):
        if isinstance(bin_string, int):
            is_negative = bin_string < 0
            bin_string = bin(bin_string)
        else:
            is_negative = bin_string.startswith("-")

        bin_string = bin_string[1:] if is_negative else bin_string
        sign = '-' if is_negative else ''

        self.binary = f"{sign}{bin_string}" if bin_string.startswith(("0b", "0B")) else f"{sign}0b{bin_string}"
        self.raw_binary = f"{sign}{bin_string[2:]}" if bin_string.startswith(("0b", "0B")) else f"{sign}{bin_string}"

        self.integer_value = int(self.binary, 2)

    def to_hex(self) -> 'Hex':
        return Hex(self.integer_value)

    def to_json(self) -> str:
        return self.binary

    def __int__(self) -> int:
        return self.integer_value

    def __str__(self) -> str:
        return self.binary

    def __bytes__(self) -> bytes:
        return bytes(self.binary, "utf-8")

    def __len__(self) -> int:
        return len(self.binary)

    def __repr__(self) -> str:
        return f"Binary(binary={self.binary})"

    def __index__(self):
        return self.__int__()

    def __eq__(self, other) -> bool:
        if isinstance(other, Binary):
            return self.binary == other.binary and self.integer_value == other.integer_value
        else:
            return False

    def __ne__(self, other) -> bool:
        if isinstance(other, Binary):
            return self.integer_value != other.integer_value or self.binary.lower() != other.binary.lower()
        else:
            return True

    def __ge__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value >= other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value >= other.integer_value
        elif isinstance(other, int):
            return self.integer_value >= other
        elif isinstance(other, str):
            return self.integer_value >= int(other, 16)
        else:
            raise TypeError(f"'>=' not supported between instances of 'Binary' and '{type(other)}'")

    def __le__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value <= other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value <= other.integer_value
        elif isinstance(other, int):
            return self.integer_value <= other
        elif isinstance(other, str):
            return self.integer_value <= int(other, 16)
        else:
            raise TypeError(f"'<=' not supported between instances of 'Binary' and '{type(other)}'")

    def __gt__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value > other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value > other.integer_value
        elif isinstance(other, int):
            return self.integer_value > other
        elif isinstance(other, str):
            return self.integer_value > int(other, 16)
        else:
            raise TypeError(f"'>' not supported between instances of 'Binary' and '{type(other)}'")

    def __lt__(self, other):
        if isinstance(other, Hex):
            return self.integer_value < other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value < other.integer_value
        elif isinstance(other, int):
            return self.integer_value < other
        elif isinstance(other, str):
            return self.integer_value < int(other, 16)
        else:
            raise TypeError(f"'<' not supported between instances of 'Binary' and '{type(other)}'")

    def __add__(self, other) -> 'Binary':
        if isinstance(other, Binary):
            return Binary(bin(self.integer_value + other.integer_value))
        elif isinstance(other, int):
            return Binary(bin(self.integer_value + other))
        elif isinstance(other, Hex):
            # You shouldn't really be adding BinString objects directly to Hex but this ensures the program won't break
            return Binary(bin(self.integer_value + other.integer_value))
        elif isinstance(other, str):
            return Binary(bin(self.integer_value + int(other, 2)))


class Hex:
    """
    Data type representing a base16 hexadecimal number.
    More intuitive and rigorous than using strings for hexadecimal numbers.

    self.hex_string : string representing the contained hexadecimal number

    self.integer_value : integer representing the base10 form of the stored hexadecimal number

    self.raw_hex : string representing contained hexadecimal number without 0x prefix
    """

    def __init__(self, hex_string: str | int):
        if isinstance(hex_string, int):
            is_negative = hex_string < 0
            hex_string = hex(hex_string)
        else:
            is_negative = hex_string.startswith("-")

        hex_string = hex_string[1:] if is_negative else hex_string
        sign = "-" if is_negative else ""
        # Removes the '0x' prefix of an input hex string if it is present
        self.hex_string = f"{sign}{hex_string}" if hex_string.startswith(("0x", "0X")) else f"{sign}0x{hex_string}"
        self.raw_hex = f"{sign}{hex_string[2:]}" if hex_string.startswith(("0x", "0X")) else f"{sign}{hex_string}"
        self.integer_value = int(self.hex_string, 16)

    def to_binary(self) -> Binary:
        return Binary(self.integer_value)

    def to_json(self) -> str:  # Possibly needs fixing
        return self.hex_string

    def __len__(self):
        return len(self.hex_string)

    def __str__(self):
        return self.hex_string

    def __int__(self):
        return self.integer_value

    def __repr__(self):
        return f"Hex(hex_string={self.hex_string})"

    def __bytes__(self):
        return bytes(self.hex_string, "utf-8")

    def __index__(self):
        return self.__int__()

    def __eq__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.hex_string.lower() == other.hex_string.lower() and self.integer_value == other.integer_value
        else:
            return False

    def __ne__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value != other.integer_value or self.hex_string.lower() != other.hex_string.lower()
        else:
            return True

    def __ge__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value >= other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value >= other.integer_value
        elif isinstance(other, int):
            return self.integer_value >= other
        elif isinstance(other, str):
            return self.integer_value >= int(other, 16)
        else:
            raise TypeError(f"'>=' not supported between instances of 'Hex' and '{type(other)}'")

    def __le__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value <= other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value <= other.integer_value
        elif isinstance(other, int):
            return self.integer_value <= other
        elif isinstance(other, str):
            return self.integer_value <= int(other, 16)
        else:
            raise TypeError(f"'<=' not supported between instances of 'Hex' and '{type(other)}'")

    def __gt__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.integer_value > other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value > other.integer_value
        elif isinstance(other, int):
            return self.integer_value > other
        elif isinstance(other, str):
            return self.integer_value > int(other, 16)
        else:
            raise TypeError(f"'>' not supported between instances of 'Hex' and '{type(other)}'")

    def __lt__(self, other):
        if isinstance(other, Hex):
            return self.integer_value < other.integer_value
        elif isinstance(other, Binary):
            return self.integer_value < other.integer_value
        elif isinstance(other, int):
            return self.integer_value < other
        elif isinstance(other, str):
            return self.integer_value < int(other, 16)
        else:
            raise TypeError(f"'<' not supported between instances of 'Hex' and '{type(other)}'")

    def __add__(self, other) -> 'Hex':
        if isinstance(other, Hex):
            return Hex(hex(self.integer_value + other.integer_value))
        elif isinstance(other, int):
            return Hex(hex(self.integer_value + other))
        elif isinstance(other, Binary):
            # You shouldn't really be adding BinString objects directly to Hex but this ensures the program won't break
            return Hex(hex(self.integer_value + other.integer_value))
        elif isinstance(other, str):
            return Hex(hex(self.integer_value + int(other, 16)))
