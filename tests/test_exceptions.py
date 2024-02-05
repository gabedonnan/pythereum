# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

from pythereum.exceptions import (
    PythereumRequestException,
    PythereumInvalidReturnException,
    PythereumDecoderException,
    PythereumEncoderException,
    PythereumSubscriptionException,
    PythereumBuilderException,
    PythereumManagerException,
    PythereumGenericException,
    PythereumABIException
)


# Test for ERPCRequestException
def test_PythereumRequestException():
    code = 404
    message = "Not Found"
    exception = PythereumRequestException(code, message)
    assert (
        str(exception)
        == f"Error {code}: {message}\nPlease consult your endpoint's documentation for info on error codes."
    )
    assert exception.code == code


# Test for ERPCInvalidReturnException
def test_PythereumInvalidReturnException():
    message = "Invalid Return"
    exception = PythereumInvalidReturnException(message)

    assert str(exception) == message


# Test for ERPCDecoderException
def test_PythereumDecoderException():
    message = "Decoder Error"
    exception = PythereumDecoderException(message)

    assert str(exception) == message


# Test for ERPCEncoderException
def test_PythereumEncoderException():
    message = "Encoder Error"
    exception = PythereumEncoderException(message)

    assert str(exception) == message


# Test for ERPCSubscriptionException
def test_PythereumSubscriptionException():
    message = "Subscription Error"
    exception = PythereumSubscriptionException(message)

    assert str(exception) == message


def test_PythereumBuilderException():
    message = "Builder Error"
    exception = PythereumBuilderException(message)

    assert str(exception) == message


def test_PythereumManagerException():
    message = "Manager Error"
    exception = PythereumManagerException(message)

    assert str(exception) == message


def test_PythereumGenericException():
    message = "Generic Error"
    exception = PythereumGenericException(message)

    assert str(exception) == message


def test_PythereumABIException():
    message = "ABI Error"
    exception = PythereumABIException(message)

    assert str(exception) == message


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
