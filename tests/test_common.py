import pytest

from pythereum.common import HexStr


def test_integer_initialization():
    hex_str = HexStr(255)
    assert str(hex_str) == "0xff"


def test_string_initialization():
    hex_str = HexStr("0xff")
    assert str(hex_str) == "0xff"

    hex_str = HexStr("ff")
    assert str(hex_str) == "0xff"


def test_invalid_string_initialization():
    with pytest.raises(ValueError):
        HexStr("0xfz")

    with pytest.raises(ValueError):
        HexStr("fz")

    with pytest.raises(ValueError):
        HexStr("0xG123")


def test_invalid_type_initialization():
    with pytest.raises(ValueError):
        HexStr(1.23)  # type: ignore

    with pytest.raises(ValueError):
        HexStr([255])  # type: ignore


def test_int_conversion():
    hex_str = HexStr("0xff")
    assert int(hex_str) == 255


def test_bytes_conversion():
    hex_str = HexStr("0xff")
    assert bytes(hex_str) == b"\xff"

    hex_str = HexStr("f")
    assert bytes(hex_str) == b"\x0f"


def test_raw_hex_property():
    hex_str = HexStr("0xff")
    assert hex_str.raw_hex == "ff"


def test_integer_value_property():
    hex_str = HexStr("0xff")
    assert hex_str.integer_value == 255


def test_repr():
    hex_str = HexStr("0xff")
    assert repr(hex_str) == "HexStr('0xff')"
