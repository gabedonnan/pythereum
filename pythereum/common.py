class Hex:
    """
    Data type representing a base16 hexadecimal number.
    More intuitive and rigorous than using strings for hexadecimal numbers.

    self.hex_string : string representing the contained hexadecimal number

    self.integer_value : integer representing the base10 form of the stored hexadecimal number

    self.raw_hex : string representing contained hexadecimal number without 0x prefix

    self.hex_bytes: bytes object representing the hex to bytes conversion of the value stored in this object
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
        self.hex_string: str = f"{sign}{hex_string}" if hex_string.startswith(("0x", "0X")) else f"{sign}0x{hex_string}"
        self.raw_hex: str = f"{sign}{hex_string[2:]}" if hex_string.startswith(("0x", "0X")) else f"{sign}{hex_string}"
        self.integer_value: int = int(self.hex_string, 16)
        self.hex_bytes: bytes = bytes.fromhex(
            self.raw_hex if len(self.raw_hex) % 2 == 0 else f"0{self.raw_hex}"
        )

    def to_json(self) -> str:  # Possibly needs fixing
        return self.hex_string

    def __len__(self):
        return len(self.hex_string)

    def __str__(self):
        return self.hex_string

    def __int__(self):
        return self.integer_value

    def __repr__(self):
        return f"Hex({self.hex_string})"

    def __bytes__(self):
        return self.hex_bytes

    def __index__(self):
        return self.__int__()

    def __eq__(self, other) -> bool:
        if isinstance(other, Hex):
            return self.hex_string.lower() == other.hex_string.lower()
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
        elif isinstance(other, int):
            return self.integer_value >= other
        elif isinstance(other, str):
            return self.integer_value >= int(other, 16)
        else:
            raise TypeError(f"'>=' not supported between instances of 'Hex' and '{type(other)}'")

    def __le__(self, other) -> bool:
        if isinstance(other, Hex):
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
        elif isinstance(other, int):
            return self.integer_value > other
        elif isinstance(other, str):
            return self.integer_value > int(other, 16)
        else:
            raise TypeError(f"'>' not supported between instances of 'Hex' and '{type(other)}'")

    def __lt__(self, other):
        if isinstance(other, Hex):
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
        elif isinstance(other, str):
            return Hex(hex(self.integer_value + int(other, 16)))
