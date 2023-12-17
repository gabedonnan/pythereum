# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import pytest

import pythereum as pye


def test_mev_bundle():
    """
    Tests the construction of MEV bundles for use with MEV boost bundle creation
    """
    sub_bundle = pye.MEVBundle(
        block="19228C",
        transactions=["0x123456789"],
        refund_addresses=["0x5fC2E691E520bbd3499f409bb9602DBA94184672"],
        refund_percentages=[100],
    )

    bundle = pye.MEVBundle(
        block="19228B",
        max_block="19228D",
        flashbots_hashes=["0x33166BBBB"],
        transactions=["0x3225", pye.HexStr(32230529), "0x0"],
        transactions_can_revert=[True, True, False, True, True, True, True, True],
        extra_mev_bundles=[sub_bundle],
        refund_addresses=["0x5fC2E691E520bbd3499f409bb9602DBA94184672"],
        refund_percentages=[100],
    )

    assert bundle == {
        "version": "v0.1",
        "inclusion": {"block": "0x19228B", "maxBlock": "0x19228D"},
        "body": [
            {"hash": "0x33166BBBB"},
            {"tx": "0x3225", "canRevert": True},
            {"tx": "0x1ebcc81", "canRevert": True},
            {"tx": "0x0", "canRevert": False},
            {
                "bundle": {
                    "version": "v0.1",
                    "inclusion": {"block": "0x19228C"},
                    "body": [{"tx": "0x123456789", "canRevert": False}],
                    "validity": {
                        "refundConfig": [
                            {
                                "address": "0x5fC2E691E520bbd3499f409bb9602DBA94184672",
                                "percent": 100,
                            }
                        ]
                    },
                }
            },
        ],
        "validity": {
            "refundConfig": [
                {
                    "address": "0x5fC2E691E520bbd3499f409bb9602DBA94184672",
                    "percent": 100,
                }
            ]
        },
    }


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
