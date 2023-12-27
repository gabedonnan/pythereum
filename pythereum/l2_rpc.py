# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

# This file contains support for L2 chains' potential extra RPC methods or in-network communication, e.g. optimism

from pythereum.rpc import EthRPC, HexStr


class OptimismRPC(EthRPC):
    """
    Class extending EthRPC for communicating between Optimism nodes
    Currently does not have support for custom object encoding
    """

    async def optimism_output_at_block(
        self,
        block_num: HexStr | int | list[HexStr] | list[int],
    ) -> list[str]:
        return await self._send_message("optimism_outputAtBlock", [block_num])

    async def optimism_sync_status(self) -> dict:
        return await self._send_message("optimism_syncStatus", [])

    async def optimism_rollup_config(self) -> dict:
        return await self._send_message("optimism_rollupConfig", [])

    async def optimism_version(self) -> str:
        return await self._send_message("optimism_version", [])

    async def opp2p_self(self) -> dict:
        return await self._send_message("opp2p_self", [])

    async def opp2p_peers(
        self,
        param: bool = True,
    ) -> dict:
        return await self._send_message("opp2p_peers", [param])


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
