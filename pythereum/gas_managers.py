# MIT License
# Copyright (C) 2023 Gabriel "gabedonnan" Donnan
# Further copyright info available at the end of the file

import statistics
from contextlib import asynccontextmanager

from pythereum.exceptions import PythereumManagerException, PythereumInvalidReturnException
from pythereum.common import EthDenomination, GasStrategy, BlockTag
from pythereum.rpc import EthRPC
from pythereum.dclasses import TransactionFull, Transaction


class NaiveGasManager:
    """
    This NaiveGasManager can fill transactions by calling:

    await nm.fill_transaction(tx, strategy=GasStrategy object)

    strategy can be replaced with dict of form:

    {"gas": GasStrategy object, "maxFeePerGas": GasStrategy object, "maxPriorityFeePerGas": GasStrategy object}
    """

    def __init__(
        self,
        rpc: EthRPC = None,
        max_gas_price: float | EthDenomination | None = None,
        max_fee_price: float | EthDenomination | None = None,
        max_priority_price: float | EthDenomination | None = None,
    ):
        self.rpc = rpc
        self.latest_transactions = None
        self.max_gas_price = int(
            max_gas_price if max_gas_price is not None else EthDenomination.milli
        )
        self.max_fee_price = int(
            max_fee_price if max_fee_price is not None else EthDenomination.milli
        )
        self.max_priority_price = int(
            max_priority_price
            if max_priority_price is not None
            else EthDenomination.milli
        )

    async def _get_latest_receipts(
        self, use_stored_results: bool = False
    ) -> list[TransactionFull]:
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
            raise PythereumInvalidReturnException(
                f"Invalid vlue: {transactions} returned from _get_latest_receipts"
            )
        return transactions

    async def suggest(
        self, strategy: GasStrategy, attribute: str, use_stored_results: bool = False
    ) -> float:
        transactions = await self._get_latest_receipts(use_stored_results)
        prices = [
            getattr(x, attribute)
            for x in transactions
            if getattr(x, attribute) is not None
        ]
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
                # Quantiles require enough data points or they will crash
                try:
                    res = statistics.quantiles(prices, n=4)[2]
                except statistics.StatisticsError:
                    res = statistics.mean(prices)
            case GasStrategy.lower_quartile_price:
                # Quantiles require enough data points or they will crash
                try:
                    res = statistics.quantiles(prices, n=4)[0]
                except statistics.StatisticsError:
                    res = statistics.mean(prices)
            case GasStrategy.custom:
                res = self.custom_pricing(prices)
            case _:
                raise PythereumManagerException(f"Invalid strategy of type {strategy} used")
        return round(res)

    async def fill_transaction(
        self,
        tx: dict | Transaction | list[dict] | list[Transaction],
        strategy: GasStrategy | dict[str, GasStrategy] = GasStrategy.mean_price,
        use_stored: bool = False,
    ) -> None:
        if isinstance(
            strategy, GasStrategy
        ):  # Allows for separation of strategy types for each type
            strategy = {
                "gas": strategy,
                "maxFeePerGas": strategy,
                "maxPriorityFeePerGas": strategy,
            }

        if isinstance(tx, list):
            for sub_tx in tx:
                sub_tx["gas"] = min(
                    await self.suggest(strategy["gas"], "gas", use_stored),
                    self.max_gas_price,
                )

                sub_tx["maxFeePerGas"] = min(
                    await self.suggest(
                        strategy["maxFeePerGas"], "max_fee_per_gas", True
                    ),
                    self.max_fee_price,
                )

                sub_tx["maxPriorityFeePerGas"] = min(
                    await self.suggest(
                        strategy["maxPriorityFeePerGas"],
                        "max_priority_fee_per_gas",
                        True,
                    ),
                    self.max_priority_price,
                )
        elif tx is not None:
            tx["gas"] = min(
                await self.suggest(strategy["gas"], "gas", use_stored),
                self.max_gas_price,
            )

            tx["maxFeePerGas"] = min(
                await self.suggest(strategy["maxFeePerGas"], "max_fee_per_gas", True),
                self.max_fee_price,
            )

            tx["maxPriorityFeePerGas"] = min(
                await self.suggest(
                    strategy["maxPriorityFeePerGas"], "max_priority_fee_per_gas", True
                ),
                self.max_priority_price,
            )

    def custom_pricing(self, prices):
        # Override this function when subclassing for custom pricing implementation
        raise PythereumManagerException("Custom pricing strategy not defined for this class")


class InformedGasManager:
    """
    This InformedGasManager can fill transactions by calling

    im.fill_transaction(tx)

    Note that this is not asynchronous like other transaction filling methods, as it relies on no external info

    To tell the gas manager the status of a transaction call one of the following functions:

    im.gas_fail()  # For when a transaction has failed due to gas too low
    im.execution_fail() # For when a transaction has failed due to an execution reversion
    im.execution_success() # For when a transaction has succeeded in execution
    """

    def __init__(
        self,
        rpc: EthRPC = None,
        max_gas_price: float | EthDenomination | None = None,
        max_fee_price: float | EthDenomination | None = None,
        max_priority_price: float | EthDenomination | None = None,
        fail_multiplier: float = 1.25,
        success_multiplier: float = 0.95,
    ):
        self.rpc = rpc
        self.latest_transactions = None
        self.prices = {"gas": 0, "maxFeePerGas": 0, "maxPriorityFeePerGas": 0}
        self.max_prices = {
            "gas": int(
                max_gas_price if max_gas_price is not None else EthDenomination.milli
            ),
            "maxFeePerGas": int(
                max_fee_price if max_fee_price is not None else EthDenomination.milli
            ),
            "maxPriorityFeePerGas": int(
                max_priority_price
                if max_priority_price is not None
                else EthDenomination.milli
            ),
        }
        self.fail_multiplier = fail_multiplier
        self.success_multiplier = success_multiplier

    async def _set_initial_price(self):
        latest_block = await self.rpc.get_block_by_number(BlockTag.latest, True)
        transactions = latest_block.transactions
        self.latest_transactions = transactions
        if len(transactions) == 0:
            raise PythereumInvalidReturnException(
                f"Invalid vlue: {transactions} returned from _get_latest_receipts"
            )
        for key, attribute in zip(
            self.prices.keys(), ("gas", "max_fee_per_gas", "max_priority_fee_per_gas")
        ):
            self.prices[key] = round(
                statistics.mean(
                    [
                        getattr(x, attribute)
                        for x in transactions
                        if getattr(x, attribute) is not None
                    ]
                )
            )

    def gas_fail(self):
        self.prices["gas"] = int(self.fail_multiplier * self.prices["gas"])

    def execution_fail(self):
        self.prices["maxPriorityFeePerGas"] = int(
            self.fail_multiplier * self.prices["maxPriorityFeePerGas"]
        )
        self.prices["maxFeePerGas"] = max(
            self.prices["maxFeePerGas"], self.prices["maxPriorityFeePerGas"]
        )

    def execution_success(self):
        self.prices["maxPriorityFeePerGas"] = int(
            self.success_multiplier * self.prices["maxPriorityFeePerGas"]
        )
        self.prices["maxFeePerGas"] = max(
            self.prices["maxFeePerGas"], self.prices["maxPriorityFeePerGas"]
        )

    def fill_transaction(self, tx: dict | Transaction | list[dict] | list[Transaction]):
        if isinstance(tx, list):
            for sub_tx in tx:
                sub_tx["gas"] = min(self.prices["gas"], self.max_prices["gas"])

                sub_tx["maxFeePerGas"] = min(
                    self.prices["maxFeePerGas"], self.max_prices["maxFeePerGas"]
                )

                sub_tx["maxPriorityFeePerGas"] = min(
                    self.prices["maxPriorityFeePerGas"],
                    self.max_prices["maxPriorityFeePerGas"],
                )
        else:
            tx["gas"] = min(self.prices["gas"], self.max_prices["gas"])

            tx["maxFeePerGas"] = min(
                self.prices["maxFeePerGas"], self.max_prices["maxFeePerGas"]
            )

            tx["maxPriorityFeePerGas"] = min(
                self.prices["maxPriorityFeePerGas"],
                self.max_prices["maxPriorityFeePerGas"],
            )


class GasManager:
    """
    Class which allows access to different kinds of gas management strategies and stores their data.

    Accepts an EthRPC instance or URL to be used for its gas management strategies
    It is recommended to start the pool for a given EthRPC instance before using a gas management strategy,
    otherwise the program will slow down as the pool will be opened and then closed
    """

    def __init__(
        self,
        rpc: "EthRPC | str | None" = None,
        max_gas_price: float | EthDenomination | None = None,
        max_fee_price: float | EthDenomination | None = None,
        max_priority_price: float | EthDenomination | None = None,
    ):
        if isinstance(rpc, str):
            rpc = EthRPC(rpc, 1)
        self.rpc = rpc
        self.max_gas_price = int(
            max_gas_price if max_gas_price is not None else EthDenomination.milli
        )
        self.max_fee_price = int(
            max_fee_price if max_fee_price is not None else EthDenomination.milli
        )
        self.max_priority_price = int(
            max_priority_price
            if max_priority_price is not None
            else EthDenomination.milli
        )
        self.naive_latest_transactions = None
        self.informed_tx_prices = {
            "gas": 0,
            "maxFeePerGas": 0,
            "maxPriorityFeePerGas": 0,
        }

    def __str__(self):
        return f"GasManager(rpc={self.rpc.__str__()})"

    def __repr__(self):
        return f"GasManager(rpc={self.rpc.__repr__()})"

    def clear_informed_info(self):
        """
        Clears stored info about informed_manager from the GasManager object
        """
        self.informed_tx_prices["gas"] = 0
        self.informed_tx_prices["maxFeePerGas"] = 0
        self.informed_tx_prices["maxPriorityFeePerGas"] = 0

    def clear_naive_info(self):
        """
        Clears stored info about naive_manager from GasManager object
        """
        self.naive_latest_transactions = None

    def clear_info(self):
        """
        Clears all stored information in the GasManager object
        """
        self.clear_naive_info()
        self.clear_informed_info()

    @asynccontextmanager
    async def naive_manager(self) -> NaiveGasManager:
        """
        Creates, yields and manages a NaiveGasManager object.

        This NaiveGasManager can fill transactions by calling

        await nm.fill_transaction(tx, strategy=GasStrategy object)

        strategy can be replaced with dict of form:
        {"gas": GasStrategy object, "maxFeePerGas": GasStrategy object, "maxPriorityFeePerGas": GasStrategy object}
        """
        naive = NaiveGasManager(self.rpc)
        connected = self.rpc.pool_connected()
        if self.naive_latest_transactions is not None:
            naive.latest_transactions = self.naive_latest_transactions
        try:
            if not connected:
                await naive.rpc.start_pool()
            yield naive
        finally:
            self.naive_latest_transactions = naive.latest_transactions
            if not connected:
                await naive.rpc.close_pool()

    @asynccontextmanager
    async def informed_manager(
        self,
        success_multiplier: float = 0.95,
        fail_multiplier: float = 1.25,
        initial_gas_price: int = None,
        initial_fee_price: int = None,
        initial_priority_fee_price: int = None,
    ) -> InformedGasManager:
        """
        Creates, yields and manages an InformedGasManager object.

        This InformedGasManager can fill transactions by calling

        im.fill_transaction(tx)

        Note that this is not asynchronous like other transaction filling methods, as it relies on no external info

        To tell the gas manager the status of a transaction call one of the following functions:

        im.gas_fail()  # For when a transaction has failed due to gas too low
        im.execution_fail() # For when a transaction has failed due to an execution reversion
        im.execution_success() # For when a transaction has succeeded in execution
        """
        informed = InformedGasManager(
            self.rpc,
            success_multiplier=success_multiplier,
            fail_multiplier=fail_multiplier,
        )
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
            informed.prices["maxPriorityFeePerGas"] = self.informed_tx_prices[
                "maxPriorityFeePerGas"
            ]

        connected = informed.rpc.pool_connected()
        try:
            if not connected:
                await informed.rpc.start_pool()
            yield informed
        finally:
            self.informed_tx_prices["gas"] = informed.prices["gas"]
            self.informed_tx_prices["maxFeePerGas"] = informed.prices["maxFeePerGas"]
            self.informed_tx_prices["maxPriorityFeePerGas"] = informed.prices[
                "maxPriorityFeePerGas"
            ]
            if not connected:
                await informed.rpc.close_pool()


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
