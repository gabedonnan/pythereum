from pythereum.exceptions import (
    ERPCRequestException,
    ERPCInvalidReturnException,
    ERPCDecoderException,
    ERPCEncoderException,
    ERPCSubscriptionException,
    ERPCBuilderException,
    ERPCManagerException,
    ERPCGenericException,
)


# Test for ERPCRequestException
def test_ERPCRequestException():
    code = 404
    message = "Not Found"
    exception = ERPCRequestException(code, message)

    assert str(exception) == f"Error {code}: {message}"
    assert exception.code == code


# Test for ERPCInvalidReturnException
def test_ERPCInvalidReturnException():
    message = "Invalid Return"
    exception = ERPCInvalidReturnException(message)

    assert str(exception) == message


# Test for ERPCDecoderException
def test_ERPCDecoderException():
    message = "Decoder Error"
    exception = ERPCDecoderException(message)

    assert str(exception) == message


# Test for ERPCEncoderException
def test_ERPCEncoderException():
    message = "Encoder Error"
    exception = ERPCEncoderException(message)

    assert str(exception) == message


# Test for ERPCSubscriptionException
def test_ERPCSubscriptionException():
    message = "Subscription Error"
    exception = ERPCSubscriptionException(message)

    assert str(exception) == message


def test_ERPCBuilderException():
    message = "Builder Error"
    exception = ERPCBuilderException(message)

    assert str(exception) == message


def test_ERPCManagerException():
    message = "Manager Error"
    exception = ERPCManagerException(message)

    assert str(exception) == message


def test_ERPCGenericException():
    message = "Generic Error"
    exception = ERPCGenericException(message)

    assert str(exception) == message
