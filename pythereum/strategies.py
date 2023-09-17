import asyncio
import statistics

from time import time
from pythereum.rpc import EthRPC, BlockTag
from pythereum.dclasses import Receipt, Transaction
from pythereum.common import HexStr

# auto get nonce for user, automatically supply gas stuff, etc.


class GasStrategy:
    def __init__(self, rpc: EthRPC):
        self.rpc = rpc
        self.latest_receipts = None
        self.storage_time = None  # The time at which the most recent storage action was taken

    async def _get_latest_receipts(self, use_stored_results: bool) -> tuple[Receipt]:
        if use_stored_results:
            transaction_receipts = self.latest_receipts
        else:
            latest_block = await self.rpc.get_block_by_number(BlockTag.latest)
            transaction_receipts = asyncio.gather(
                *(self.rpc.get_transaction_receipt(transaction) for transaction in latest_block.transactions)
            )
            self.latest_receipts = transaction_receipts
            self.storage_time = time()
        return transaction_receipts

    async def min_price(self, use_stored_results: bool = False) -> int:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return min([x.gas_used for x in transaction_receipts])

    async def max_price(self, use_stored_results: bool = False) -> int:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return max([x.gas_used for x in transaction_receipts])

    async def median_price(self, use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.median([x.gas_used for x in transaction_receipts])

    async def mean_price(self, use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.mean([x.gas_used for x in transaction_receipts])

    async def mode_price(self, use_stored_results: bool = False) -> int:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.mode([x.gas_used for x in transaction_receipts])

    async def upper_quartile_price(self, use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.quantiles([x.gas_used for x in transaction_receipts], n=4)[2]

    async def lower_quartile_price(self, use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.quantiles([x.gas_used for x in transaction_receipts], n=4)[0]

    async def percentile_price(self, percentile: int, use_stored_results: bool = False) -> float:
        """
        Gets the lower nth percentile, where 0 will be the lowest value and 98 will be the highest
        """
        percentile = min(max(percentile, 0), 98)
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.quantiles([x.gas_used for x in transaction_receipts], n=100)[percentile]

    @property
    def storage_age(self):
        """
        The time elapsed since the most recent snapshot was taken
        """
        return time() - self.storage_time


class NonceManager:
    def __init__(self, rpc: EthRPC):
        self.rpc = rpc
        self.nonces = {}

    def __getitem__(self, key):
        return self.nonces[HexStr(key)]

    def __setitem__(self, key, value):
        self.nonces[HexStr(key)] = value

    async def next_nonce(self, address: str | HexStr) -> int:
        address = HexStr(address)
        if address in self.nonces:
            self.nonces[address] += 1
            return self.nonces[address]
        else:
            self.nonces[address] = await self.rpc.get_transaction_count(address)
            return self.nonces[address]

    async def fill_transaction(self, tx: Transaction) -> Transaction:
        tx["nonce"] = await self.next_nonce(tx["from"])
        return tx

