import asyncio
import statistics

from math import inf
from time import time
from pythereum.rpc import EthRPC, BlockTag
from pythereum.dclasses import Receipt
from pythereum.exceptions import ERPCInvalidReturnException

# auto get nonce for user, automatically supply gas stuff, etc.


class GasStrategy:
    def __init__(self, rpc: EthRPC):
        self.rpc = rpc
        self.latest_receipts = None
        self.storage_time = None  # The time at which the most recent storage action was taken

    async def _get_latest_receipts(self, use_stored_results: bool) -> tuple[Receipt]:
        """
        Returns a tuple of the latest transaction receipts.
        These are gotten by getting the latest block info and requesting transaction receipts for each transaction.
        To avoid doing this for every call, there is the option to use stored results from the most recent request.
        """
        if use_stored_results:
            transaction_receipts = self.latest_receipts
        else:
            latest_block = await self.rpc.get_block_by_number(BlockTag.latest)
            transaction_receipts = await asyncio.gather(
                *(self.rpc.get_transaction_receipt(transaction) for transaction in latest_block.transactions)
            )
            self.latest_receipts = transaction_receipts
            self.storage_time = time()
        if len(transaction_receipts) == 0:
            raise ERPCInvalidReturnException(f"Invalid vlue: {transaction_receipts} returned from _get_latest_receipts")
        return transaction_receipts

    async def min_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> int:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return min([x.__getattribute__(attribute) for x in transaction_receipts])

    async def max_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> int:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return max([x.__getattribute__(attribute) for x in transaction_receipts])

    async def median_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.median([x.__getattribute__(attribute) for x in transaction_receipts])

    async def mean_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.mean([x.__getattribute__(attribute) for x in transaction_receipts])

    async def mode_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> int:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.mode([x.__getattribute__(attribute) for x in transaction_receipts])

    async def upper_quartile_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.quantiles([x.__getattribute__(attribute) for x in transaction_receipts], n=4)[2]

    async def lower_quartile_price(self, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> float:
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.quantiles([x.__getattribute__(attribute) for x in transaction_receipts], n=4)[0]

    async def percentile_price(self, percentile: int, attribute: str = "effective_gas_price", use_stored_results: bool = False) -> float:  # noqa
        """
        Gets the lower nth percentile, where 0 will be the lowest value and 98 will be the highest
        """
        percentile = min(max(percentile, 0), 98)
        transaction_receipts = await self._get_latest_receipts(use_stored_results)
        return statistics.quantiles([x.__getattribute__(attribute) for x in transaction_receipts], n=100)[percentile]

    @property
    def storage_age(self):
        """
        The time elapsed since the most recent snapshot was taken
        If no snapshots have been taken the return value will be infinity
        """
        if self.storage_time is None:
            return inf
        return time() - self.storage_time



