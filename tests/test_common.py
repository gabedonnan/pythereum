# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import pytest

from pythereum import HexStr


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
