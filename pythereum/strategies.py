import statistics

from math import inf
from time import time
from enum import Enum
from pythereum.rpc import EthRPC, BlockTag
from pythereum.dclasses import TransactionFull, Transaction
from pythereum.exceptions import ERPCInvalidReturnException

# auto get nonce for user, automatically supply gas stuff, etc.


class GasStrategy(Enum):
    min_price = 0
    max_price = 1
    median_price = 2
    mean_price = 3
    mode_price = 4
    upper_quartile_price = 5
    lower_quartile_price = 6


class GasManager:
    def __init__(self, rpc: EthRPC):
        self.rpc = rpc
        self.latest_transactions = None
        self.storage_time = None  # The time at which the most recent storage action was taken

    async def _get_latest_receipts(self, use_stored_results: bool) -> list[TransactionFull]:
        """
        Returns a tuple of the latest transaction receipts.
        These are gotten by getting the latest block info and requesting transaction receipts for each transaction.
        To avoid doing this for every call, there is the option to use stored results from the most recent request.
        """
        if use_stored_results:
            transactions = self.latest_transactions
        else:
            latest_block = await self.rpc.get_block_by_number(BlockTag.latest, True)
            transactions = latest_block.transactions
            self.latest_transactions = transactions
            self.storage_time = time()
        if len(transactions) == 0:
            raise ERPCInvalidReturnException(f"Invalid vlue: {transactions} returned from _get_latest_receipts")
        return transactions

    async def suggest(
        self,
        strategy: GasStrategy = GasStrategy.mean_price,
        attribute: str = "gas",
        use_stored_results: bool = False
    ) -> float:
        transactions = await self._get_latest_receipts(use_stored_results)
        prices = [x.__getattribute__(attribute) for x in transactions]
        match strategy:
            case GasStrategy.min_price:
                return min(prices)
            case GasStrategy.max_price:
                return max(prices)
            case GasStrategy.median_price:
                return statistics.median(prices)
            case GasStrategy.mean_price:
                return statistics.mean(prices)
            case GasStrategy.upper_quartile_price:
                return statistics.quantiles(prices, n=4)[2]
            case GasStrategy.lower_quartile_price:
                return statistics.quantiles(prices, n=4)[0]

    async def fill_transaction(
        self,
        tx: Transaction | list[Transaction],
        strategy: GasStrategy = GasStrategy.mean_price | dict[str, GasStrategy]
    ) -> None:
        if isinstance(strategy, GasStrategy):  # Allows for separation of strategy types for each type
            strategy = {"gas": strategy, "maxFeePerGas": strategy, "maxPriorityFeePerGas": strategy}
        if isinstance(tx, list):
            for sub_tx in tx:
                sub_tx["gas"] = await self.suggest(strategy["gas"], "gas", False)
                sub_tx["maxFeePerGas"] = await self.suggest(strategy["maxFeePerGas"], "maxFeePerGas", True)
                sub_tx["maxPriorityFeePerGas"] = await self.suggest(
                    strategy["maxPriorityFeePerGas"], "maxPriorityFeePerGas", True
                )
        elif tx is not None:
            tx["gas"] = await self.suggest(strategy["gas"], "gas", False)
            tx["maxFeePerGas"] = await self.suggest(strategy["maxFeePerGas"], "maxFeePerGas", True)
            tx["maxPriorityFeePerGas"] = await self.suggest(
                strategy["maxPriorityFeePerGas"], "maxPriorityFeePerGas", True
            )

    @property
    def storage_age(self):
        """
        The time elapsed since the most recent snapshot was taken
        If no snapshots have been taken the return value will be infinity
        """
        if self.storage_time is None:
            return inf
        return time() - self.storage_time
