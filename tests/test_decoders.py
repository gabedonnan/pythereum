# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import pytest

from pythereum.dclasses import (
    hex_encoder,
    log_encoder,
    log_list_encoder,
    access_list_encoder,
    transaction_encoder,
    hex_int_encoder,
    hex_list_encoder,
    transaction_list_encoder,
    access_encoder,
    hex_list_decoder,
    log_list_decoder,
    access_list_decoder,
    transaction_list_decoder,
    hex_int_decoder,
    hex_decoder,
    log_decoder,
    transaction_decoder,
    access_decoder,
    ERPCDecoderException,
    ERPCEncoderException,
    HexStr,
    Log,
    Access,
    TransactionFull,
)


def test_hex_int_decoder():
    assert hex_int_decoder("0x0") == 0
    assert hex_int_decoder("0") == 0
    assert hex_int_decoder("0xaaaa") == 43690
    assert hex_int_decoder(None) is None
    with pytest.raises(ERPCDecoderException) as info:
        hex_int_decoder("zzzzz")


def test_hex_int_encoder():
    assert hex_int_encoder(0) == "0x0"
    assert hex_int_encoder(43690) == "0xaaaa"
    assert hex_int_encoder(None) is None
    with pytest.raises(ERPCEncoderException) as info:
        hex_int_encoder("zzzzz")


def test_hex_decoder():
    assert hex_decoder("0x0") == HexStr("0x0")
    assert hex_decoder("0") == HexStr("0x0")
    assert hex_decoder("0xaaaa") == HexStr("0xaaaa")
    assert hex_decoder(None) is None
    with pytest.raises(ERPCDecoderException) as info:
        hex_decoder("zzzzz")


def test_hex_encoder():
    assert hex_encoder(HexStr("0x0")) == "0x0"
    assert hex_encoder(HexStr("0")) == "0x0"
    assert hex_encoder(HexStr("0xaaaa")) == "0xaaaa"
    assert hex_encoder(None) is None


def test_hex_list_decoder():
    assert hex_list_decoder(["0x0"]) == [HexStr("0x0")]
    assert hex_list_decoder(["0", "0"]) == [HexStr("0x0"), HexStr("0x0")]
    assert hex_list_decoder(["0xaaaa", "0xaaaa"]) == [
        HexStr("0xaaaa"),
        HexStr("0xaaaa"),
    ]
    assert hex_list_decoder(None) is None
    with pytest.raises(ERPCDecoderException) as info:
        hex_list_decoder(["zzzzz"])


def test_hex_list_encoder():
    assert hex_list_encoder([HexStr("0x0")]) == ["0x0"]
    assert hex_list_encoder([HexStr("0x0"), HexStr("0")]) == ["0x0", "0x0"]
    assert hex_list_encoder([HexStr("0xaaaa"), HexStr("0xaaaa")]) == [
        "0xaaaa",
        "0xaaaa",
    ]
    assert hex_list_encoder(None) is None


def test_log_decoder():
    assert log_decoder(None) is None
    assert log_decoder(
        {
            "address": "0x0",
            "blockHash": None,
            "blockNumber": None,
            "data": None,
            "logIndex": None,
            "topics": None,
            "transactionHash": None,
            "transactionIndex": None,
            "removed": None,
        }
    ) == Log(
        address=HexStr("0x0"),
        block_hash=None,
        block_number=None,
        data=None,
        log_index=None,
        topics=None,
        transaction_hash=None,
        transaction_index=None,
        removed=None,
    )


def test_log_encoder():
    assert log_encoder(None) is None
    assert log_encoder(
        Log(
            address=HexStr("0x0"),
            block_hash=None,
            block_number=None,
            data=None,
            log_index=None,
            topics=None,
            transaction_hash=None,
            transaction_index=None,
            removed=None,
        )
    ) == {
        "address": "0x0",
        "blockHash": None,
        "blockNumber": None,
        "data": None,
        "logIndex": None,
        "topics": None,
        "transactionHash": None,
        "transactionIndex": None,
        "removed": None,
    }


def test_log_list_decoder():
    assert log_list_decoder(None) is None
    assert log_list_decoder(
        [
            {
                "address": "0x0",
                "blockHash": None,
                "blockNumber": None,
                "data": None,
                "logIndex": None,
                "topics": None,
                "transactionHash": None,
                "transactionIndex": None,
                "removed": None,
            }
        ]
    ) == [
        Log(
            address=HexStr("0x0"),
            block_hash=None,
            block_number=None,
            data=None,
            log_index=None,
            topics=None,
            transaction_hash=None,
            transaction_index=None,
            removed=None,
        )
    ]


def test_log_list_encoder():
    assert log_list_encoder(None) is None
    assert log_list_encoder(
        [
            Log(
                address=HexStr("0x0"),
                block_hash=None,
                block_number=None,
                data=None,
                log_index=None,
                topics=None,
                transaction_hash=None,
                transaction_index=None,
                removed=None,
            )
        ]
    ) == [
        {
            "address": "0x0",
            "blockHash": None,
            "blockNumber": None,
            "data": None,
            "logIndex": None,
            "topics": None,
            "transactionHash": None,
            "transactionIndex": None,
            "removed": None,
        }
    ]


def test_access_decoder():
    assert access_decoder(None) is None
    assert access_decoder({"address": "0x0", "storageKeys": ["0x0"]}) == Access(
        address=HexStr("0x0"), storage_keys=[HexStr("0x0")]
    )


def test_access_encoder():
    assert access_encoder(None) is None
    assert access_encoder(
        Access(address=HexStr("0x0"), storage_keys=[HexStr("0x0")])
    ) == {"address": "0x0", "storageKeys": ["0x0"]}


def test_access_list_decoder():
    assert access_list_decoder(None) is None
    assert access_list_decoder([{"address": "0x0", "storageKeys": ["0x0"]}]) == [
        Access(address=HexStr("0x0"), storage_keys=[HexStr("0x0")])
    ]


def test_access_list_encoder():
    assert access_list_encoder(None) is None
    assert access_list_encoder(
        [Access(address=HexStr("0x0"), storage_keys=[HexStr("0x0")])]
    ) == [{"address": "0x0", "storageKeys": ["0x0"]}]


def test_transaction_decoder():
    assert transaction_decoder(None) is None
    assert transaction_decoder(
        {
            "blockHash": None,
            "blockNumber": None,
            "from": None,
            "gas": None,
            "gasPrice": None,
            "maxFeePerGas": None,
            "maxPriorityFeePerGas": None,
            "hash": None,
            "input": None,
            "nonce": None,
            "to": None,
            "transactionIndex": None,
            "value": None,
            "type": None,
            "accessList": None,
            "chainId": None,
            "v": None,
            "r": None,
            "s": None,
        }
    ) == TransactionFull(
        block_hash=None,
        block_number=None,
        from_address=None,
        gas=None,
        gas_price=None,
        max_fee_per_gas=None,
        max_priority_fee_per_gas=None,
        hash=None,
        input=None,
        nonce=None,
        to_address=None,
        transaction_index=None,
        value=None,
        type=None,
        access_list=None,
        chain_id=None,
        v=None,
        r=None,
        s=None,
    )


def test_transaction_encoder():
    assert transaction_encoder(None) is None
    assert transaction_encoder(
        TransactionFull(
            block_hash=None,
            block_number=None,
            from_address=None,
            gas=None,
            gas_price=None,
            max_fee_per_gas=None,
            max_priority_fee_per_gas=None,
            hash=None,
            input=None,
            nonce=None,
            to_address=None,
            transaction_index=None,
            value=None,
            type=None,
            access_list=None,
            chain_id=None,
            v=None,
            r=None,
            s=None,
        )
    ) == {
        "blockHash": None,
        "blockNumber": None,
        "from": None,
        "gas": None,
        "gasPrice": None,
        "maxFeePerGas": None,
        "maxPriorityFeePerGas": None,
        "hash": None,
        "input": None,
        "nonce": None,
        "to": None,
        "transactionIndex": None,
        "value": None,
        "type": None,
        "accessList": None,
        "chainId": None,
        "v": None,
        "r": None,
        "s": None,
    }


def test_transaction_list_decoder():
    assert transaction_list_decoder(None) is None
    assert transaction_list_decoder(
        [
            {
                "blockHash": None,
                "blockNumber": None,
                "from": None,
                "gas": None,
                "gasPrice": None,
                "maxFeePerGas": None,
                "maxPriorityFeePerGas": None,
                "hash": None,
                "input": None,
                "nonce": None,
                "to": None,
                "transactionIndex": None,
                "value": None,
                "type": None,
                "accessList": None,
                "chainId": None,
                "v": None,
                "r": None,
                "s": None,
            }
        ]
    ) == [
        TransactionFull(
            block_hash=None,
            block_number=None,
            from_address=None,
            gas=None,
            gas_price=None,
            max_fee_per_gas=None,
            max_priority_fee_per_gas=None,
            hash=None,
            input=None,
            nonce=None,
            to_address=None,
            transaction_index=None,
            value=None,
            type=None,
            access_list=None,
            chain_id=None,
            v=None,
            r=None,
            s=None,
        )
    ]


def test_transaction_list_encoder():
    assert transaction_list_encoder(None) is None
    assert transaction_list_encoder(
        [
            TransactionFull(
                block_hash=None,
                block_number=None,
                from_address=None,
                gas=None,
                gas_price=None,
                max_fee_per_gas=None,
                max_priority_fee_per_gas=None,
                hash=None,
                input=None,
                nonce=None,
                to_address=None,
                transaction_index=None,
                value=None,
                type=None,
                access_list=None,
                chain_id=None,
                v=None,
                r=None,
                s=None,
            )
        ]
    ) == [
        {
            "blockHash": None,
            "blockNumber": None,
            "from": None,
            "gas": None,
            "gasPrice": None,
            "maxFeePerGas": None,
            "maxPriorityFeePerGas": None,
            "hash": None,
            "input": None,
            "nonce": None,
            "to": None,
            "transactionIndex": None,
            "value": None,
            "type": None,
            "accessList": None,
            "chainId": None,
            "v": None,
            "r": None,
            "s": None,
        }
    ]


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
