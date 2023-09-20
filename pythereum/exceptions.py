class ERPCBaseException(Exception):
    """
    Base exception class for Ethereum RPC interactions.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ERPCRequestException(ERPCBaseException):
    """
    Raised when an error is returned from the Ethereum RPC.
    """
    def __init__(self, code: int, message: str = "Generic ERPC Error"):
        self.code = code  # Error code, e.g., HTTP error code or custom ERPC code
        full_message = f"Error {code}: {message}"
        super().__init__(full_message)


class ERPCInvalidReturnException(ERPCBaseException):
    """
    Raised when the Ethereum RPC returns a value which is incorrectly formatted.
    """


class ERPCDecoderException(ERPCBaseException):
    """
    Raised when invalid data is input to a decoder and an error is thrown.
    """


class ERPCEncoderException(ERPCBaseException):
    """
    Raised when invalid data is input to an encoder and an error is thrown.
    """


class ERPCSubscriptionException(ERPCBaseException):
    """
    Raised when a subscription request is rejected by a host or for other generic subscription errors.
    """


class ERPCBuilderException(ERPCBaseException):
    """
    Raised for exceptions related to builders and the BuilderRPC
    """


class ERPCManagerException(ERPCBaseException):
    """
    Raised for exceptions related to manager classes such as nonce managers or gas managers
    """