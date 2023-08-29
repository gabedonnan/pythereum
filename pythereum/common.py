class HexStr(str):
    """
    Data type representing a base16 hexadecimal number.
    Extends the functionality of the default string type to support hex operations and functionality

    self.integer_value : returns integer representing the base10 form of the stored hexadecimal number

    self.raw_hex : returns string representing contained hexadecimal number without 0x prefix

    self.hex_bytes: returns bytes object representing the hex to bytes conversion of the value stored in this object
    """
    def __new__(cls, *args, **kwargs):
        arg = args[0]
        if isinstance(arg, str):
            arg = arg if arg.startswith(("0x", "0X")) else f"0x{arg}"
        elif isinstance(arg, int):
            arg = hex(arg)
        args = (arg,)
        new_instance = super().__new__(cls, *args, **kwargs)
        return new_instance

    def __int__(self):
        return int(self, 16)

    def __repr__(self):
        return f"h'{self}'"

    def __bytes__(self):
        return bytes.fromhex(self.raw_hex() if len(self) % 2 == 0 else f"0{self.raw_hex()}")

    def hex_bytes(self):
        return self.__bytes__()

    def raw_hex(self):
        return self[2:]

    def integer_value(self):
        return self.__int__()
