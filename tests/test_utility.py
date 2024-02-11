# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import pytest

from pythereum import convert_eth, EthDenomination, to_checksum_address


def test_eth_conversion():
    assert convert_eth(1e18, EthDenomination.wei, EthDenomination.eth) == 1
    assert convert_eth(1, EthDenomination.eth, EthDenomination.wei) == 1e18

    assert convert_eth(0, EthDenomination.eth, EthDenomination.eth) == 0

    assert convert_eth(1e18, "wei", "eth") == 1
    assert convert_eth(1, "eth", "wei") == 1e18


def test_to_checksum_address():
    assert (
        to_checksum_address("0x5fC2E691E520bbd3499f409bb9602DBA94184672".lower())
        == "0x5fC2E691E520bbd3499f409bb9602DBA94184672"
    )

    assert (
        to_checksum_address("5fC2E691E520bbd3499f409bb9602DBA94184672".lower())
        == "0x5fC2E691E520bbd3499f409bb9602DBA94184672"
    )

    assert (
        to_checksum_address("0x5fC2E691E520bbd3499f409bb9602DBA94184672")
        == "0x5fC2E691E520bbd3499f409bb9602DBA94184672"
    )


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
