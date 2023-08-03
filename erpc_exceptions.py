class ERPCRequestException(Exception):
    """
    Raised when an error is returned from the Ethereum RPC
    """

    def __init__(self, code: int, message: str = "Generic ERPC Error"):
        self.code = code
        self.message = message
        super().__init__(f"Error {code}: " + self.message)


class ERPCInvalidReturnException(Exception):
    """
    Raised when the Ethereum RPC returns a value which is incorrectly formatted
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ERPCDecoderException(Exception):
    """
    Raised when invalid data is input to a decoder and an error is thrown
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ERPCEncoderException(Exception):
    """
    Raised when invalid data is input to an encoder and an error is thrown
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
