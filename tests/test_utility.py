import pytest

from pythereum import convert_eth, EthDenomination


def test_eth_conversion():
    assert convert_eth(1e18, EthDenomination.wei, EthDenomination.eth) == 1
    assert convert_eth(1, EthDenomination.eth, EthDenomination.wei) == 1e18

    assert convert_eth(0, EthDenomination.eth, EthDenomination.eth) == 0

    assert convert_eth(1e18, "wei", "eth") == 1
    assert convert_eth(1, "eth", "wei") == 1e18
