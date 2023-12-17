# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file


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
        full_message = f"Error {code}: {message}\nPlease consult your endpoint's documentation for info on error codes."
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


class ERPCGenericException(ERPCBaseException):
    """
    Raised for exceptions which do not fall into any of the above categories, things like utility functions will use it
    """


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
