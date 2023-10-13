import statistics
from contextlib import asynccontextmanager

from pythereum.exceptions import ERPCManagerException, ERPCInvalidReturnException
from pythereum.common import EthDenomination, GasStrategy, BlockTag
from pythereum.rpc import EthRPC
from pythereum.dclasses import TransactionFull, Transaction


class NaiveGasManager:
    def __init__(
            self,
            rpc: EthRPC = None,
            max_gas_price: float | EthDenomination | None = None,
            max_fee_price: float | EthDenomination | None = None,
            max_priority_price: float | EthDenomination | None = None
    ):
        self.rpc = rpc
        self.latest_transactions = None
        self.max_gas_price = int(max_gas_price if max_gas_price is not None else EthDenomination.milli)
        self.max_fee_price = int(max_fee_price if max_fee_price is not None else EthDenomination.milli)
        self.max_priority_price = int(max_priority_price if max_priority_price is not None else EthDenomination.milli)

    async def _get_latest_receipts(self, use_stored_results: bool = False) -> list[TransactionFull]:
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
        if len(transactions) == 0:
            raise ERPCInvalidReturnException(f"Invalid vlue: {transactions} returned from _get_latest_receipts")
        return transactions

    async def suggest(
        self,
        strategy: GasStrategy,
        attribute: str,
        use_stored_results: bool = False
    ) -> float:
        transactions = await self._get_latest_receipts(use_stored_results)
        prices = [x.__getattribute__(attribute) for x in transactions if x.__getattribute__(attribute) is not None]
        match strategy:
            case GasStrategy.min_price:
                res = min(prices)
            case GasStrategy.max_price:
                res = max(prices)
            case GasStrategy.median_price:
                res = statistics.median(prices)
            case GasStrategy.mean_price:
                res = statistics.mean(prices)
            case GasStrategy.mode_price:
                res = statistics.mode(prices)
            case GasStrategy.upper_quartile_price:
                try:
                    res = statistics.quantiles(prices, n=4)[2]
                except statistics.StatisticsError:
                    res = statistics.mean(prices)
            case GasStrategy.lower_quartile_price:
                try:
                    res = statistics.quantiles(prices, n=4)[0]
                except statistics.StatisticsError:
                    res = statistics.mean(prices)
            case GasStrategy.custom:
                res = self.custom_pricing(prices)
            case _:
                raise ERPCManagerException(f"Invalid strategy of type {strategy} used")
        return round(res)

    async def fill_transaction(
        self,
        tx: dict | Transaction | list[dict] | list[Transaction],
        strategy: GasStrategy | dict[str, GasStrategy] = GasStrategy.mean_price,
        use_stored: bool = False
    ) -> None:
        if isinstance(strategy, GasStrategy):  # Allows for separation of strategy types for each type
            strategy = {"gas": strategy, "maxFeePerGas": strategy, "maxPriorityFeePerGas": strategy}

        if isinstance(tx, list):
            for sub_tx in tx:
                sub_tx["gas"] = min(await self.suggest(strategy["gas"], "gas", use_stored), self.max_gas_price)
                sub_tx["maxFeePerGas"] = min(
                    await self.suggest(strategy["maxFeePerGas"], "max_fee_per_gas", True),
                    self.max_fee_price
                )
                sub_tx["maxPriorityFeePerGas"] = min(
                    await self.suggest(strategy["maxPriorityFeePerGas"], "max_priority_fee_per_gas", True),
                    self.max_priority_price
                )
        elif tx is not None:
            tx["gas"] = min(await self.suggest(strategy["gas"], "gas", use_stored), self.max_gas_price)
            tx["maxFeePerGas"] = min(
                await self.suggest(strategy["maxFeePerGas"], "max_fee_per_gas", True),
                self.max_fee_price
            )
            tx["maxPriorityFeePerGas"] = min(
                await self.suggest(strategy["maxPriorityFeePerGas"], "max_priority_fee_per_gas", True),
                self.max_priority_price
            )

    def custom_pricing(self, prices):
        # Override this function when subclassing for custom pricing implementation
        raise ERPCManagerException("Custom pricing strategy not defined for this class")


class InformedGasManager:
    def __init__(
            self,
            rpc: EthRPC = None,
            max_gas_price: float | EthDenomination | None = None,
            max_fee_price: float | EthDenomination | None = None,
            max_priority_price: float | EthDenomination | None = None,
            fail_multiplier: float = 1.25,
            success_multiplier: float = 0.95
    ):
        self.rpc = rpc
        self.latest_transactions = None
        self.prices = {"gas": 0, "maxFeePerGas": 0, "maxPriorityFeePerGas": 0}
        self.max_prices = {
            "gas": int(max_gas_price if max_gas_price is not None else EthDenomination.milli),
            "maxFeePerGas": int(max_fee_price if max_fee_price is not None else EthDenomination.milli),
            "maxPriorityFeePerGas": int(max_priority_price if max_priority_price is not None else EthDenomination.milli)
        }
        self.fail_multiplier = fail_multiplier
        self.success_multiplier = success_multiplier

    async def _set_initial_price(self):
        latest_block = await self.rpc.get_block_by_number(BlockTag.latest, True)
        transactions = latest_block.transactions
        self.latest_transactions = transactions
        if len(transactions) == 0:
            raise ERPCInvalidReturnException(f"Invalid vlue: {transactions} returned from _get_latest_receipts")
        for key, attribute in zip(self.prices.keys(), ("gas", "max_fee_per_gas", "max_priority_fee_per_gas")):
            self.prices[key] = round(statistics.mean(
                [x.__getattribute__(attribute) for x in transactions if x.__getattribute__(attribute) is not None]
            ))

    def gas_fail(self):
        self.prices["gas"] *= self.fail_multiplier

    def execution_fail(self):
        self.prices["maxPriorityFeePerGas"] *= self.fail_multiplier
        self.prices["maxFeePerGas"] = max(self.prices["maxFeePerGas"], self.prices["maxPriorityFeePerGas"])

    def execution_success(self):
        self.prices["maxPriorityFeePerGas"] *= self.success_multiplier
        self.prices["maxFeePerGas"] = max(self.prices["maxFeePerGas"], self.prices["maxPriorityFeePerGas"])

    def fill_transaction(
        self,
        tx: dict | Transaction | list[dict] | list[Transaction]
    ):
        if isinstance(tx, list):
            for sub_tx in tx:
                sub_tx["gas"] = min(
                    self.prices["gas"], self.max_prices["gas"]
                )

                sub_tx["maxFeePerGas"] = min(
                    self.prices["maxFeePerGas"], self.max_prices["maxFeePerGas"]
                )

                sub_tx["maxPriorityFeePerGas"] = min(
                    self.prices["maxPriorityFeePerGas"], self.max_prices["maxPriorityFeePerGas"]
                )
        else:
            tx["gas"] = min(
                self.prices["gas"], self.max_prices["gas"]
            )

            tx["maxFeePerGas"] = min(
                self.prices["maxFeePerGas"], self.max_prices["maxFeePerGas"]
            )

            tx["maxPriorityFeePerGas"] = min(
                self.prices["maxPriorityFeePerGas"], self.max_prices["maxPriorityFeePerGas"]
            )


class GasManager:
    def __init__(
        self,
        rpc: "EthRPC | str | None" = None,
        max_gas_price: float | EthDenomination | None = None,
        max_fee_price: float | EthDenomination | None = None,
        max_priority_price: float | EthDenomination | None = None
    ):
        if isinstance(rpc, str):
            rpc = EthRPC(rpc, 1)
        self.rpc = rpc
        self.max_gas_price = int(max_gas_price if max_gas_price is not None else EthDenomination.milli)
        self.max_fee_price = int(max_fee_price if max_fee_price is not None else EthDenomination.milli)
        self.max_priority_price = int(max_priority_price if max_priority_price is not None else EthDenomination.milli)
        self.naive_latest_transactions = None
        self.informed_tx_prices = {"gas": 0, "maxFeePerGas": 0, "maxPriorityFeePerGas": 0}

    @asynccontextmanager
    async def naive_manager(self):
        naive = NaiveGasManager(self.rpc)
        connected = self.rpc.pool_connected()
        try:
            if not connected:
                await naive.rpc.start_pool()
            yield naive
        finally:
            if not connected:
                await naive.rpc.close_pool()

    @asynccontextmanager
    async def informed_manager(
            self,
            success_multiplier: float = 0.95,
            fail_multiplier: float = 1.25,
            initial_gas_price: int = None,
            initial_fee_price: int = None,
            initial_priority_fee_price: int = None
    ) -> InformedGasManager:
        informed = InformedGasManager(self.rpc, success_multiplier=success_multiplier, fail_multiplier=fail_multiplier)
        await informed._set_initial_price()

        if initial_gas_price is not None:
            informed.prices["gas"] = initial_gas_price
        elif self.informed_tx_prices["gas"] != 0:
            informed.prices["gas"] = self.informed_tx_prices["gas"]

        if initial_fee_price is not None:
            informed.prices["maxFeePerGas"] = initial_fee_price
        elif self.informed_tx_prices["maxFeePerGas"] != 0:
            informed.prices["maxFeePerGas"] = self.informed_tx_prices["maxFeePerGas"]

        if initial_priority_fee_price is not None:
            informed.prices["maxPriorityFeePerGas"] = initial_priority_fee_price
        elif self.informed_tx_prices["maxPriorityFeePerGas"] != 0:
            informed.prices["maxPriorityFeePerGas"] = self.informed_tx_prices["maxPriorityFeePerGas"]

        connected = informed.rpc.pool_connected()
        try:
            if not connected:
                await informed.rpc.start_pool()
            yield informed
        finally:
            self.informed_tx_prices["gas"] = informed.prices["gas"]
            self.informed_tx_prices["maxFeePerGas"] = informed.prices["maxFeePerGas"]
            self.informed_tx_prices["maxPriorityFeePerGas"] = informed.prices["maxPriorityFeePerGas"]
            if not connected:
                await informed.rpc.close_pool()
