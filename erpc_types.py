class Hex:
    def __init__(self, hex_string: str):
        self.string = hex_string[2:] if hex_string.startswith(("0x", "0X")) else hex_string
        self.binary = bin(int(self.string, 16))[2:]
        self.base = len(self.string)

    def __len__(self):
        return self.base

    def __str__(self):
        return self.string

    def __hex__(self):
        return f"0x{self.string}"

    def __int__(self):
        return int(self.string, 16)

    def __repr__(self):
        return f"Hex(base={self.base}, string={self.string})"

    def __bytes__(self):
        return bytes(self.string, "utf-8")


