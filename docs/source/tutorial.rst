========
Tutorial
========

The Basics
==========

At it's core Pythereum provides functionality to interact efficiently with Ethereum nodes via the Ethereum JSON RPC API.
This is primarily done with the EthRPC class, and that will be the focus of this section of the tutorial.

In order to get started we need an `Ethereum endpoint <https://ethereum.org/en/developers/docs/nodes-and-clients/>`_ to connect to, for which you will need a connection URL.
This URL can use the following prefixes for fast websocketed functionality:

* wss://
* ws://

For http connection you can also use, be aware HTTP connections will not be able to make use of websocket pooling:

* https://
* http://

For this tutorial I will be using a personal node I connect to via websockets which will be referred to as "ENDPOINT_URL".

Much of Pythereum's functionality is asynchronous, which means we will need the library asyncio to run our code.

For our first block of code let's try and get the number of the most recent block in the chain.

.. code-block:: python
  :linenos:

  import asyncio
  from pythereum import EthRPC

  # Note we use "async def" here as we use asynchronous code in this function
  async def my_first_rpc_connection():
    # Similarly we use "async with" here to declare our rpc connection
    # If we are using an http or https url, we should include the following argument to EthRPC:
    #   use_socket_pool=False
    async with EthRPC(ENDPOINT_URL) as rpc:
      # We must "await" the result of our function call, as we are waiting for our endpoint to respond
      block_num = await rpc.get_block_number()

    # Verify that the return is indeed an integer, e.g. 18455132
    print(block_num)

  if __name__ == "__main__":
    asyncio.run(my_first_rpc_connection())

In this example we do a couple things:

* We declare a connection to our RPC endpoint using:

"async with `EthRPC(ENDPOINT_URL) <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.rpc.EthRPC>`_ as rpc:"

This line starts up a pool of websockets to connect to the given endpoint, when we exit the scope of
"async with", the connection pool is automatically closed.

Any function we call using the "rpc" object we create will use the pool of websockets here to communicate with our endpoint.

* We use our connection to call `"get_block_number" <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.rpc.EthRPC.get_block_number>`_

Pythereum manages the parameters used and the return types gotten from the function.

Now what if we wanted to do something a little more advanced than getting the latest block number?

Maybe instead of the block number we wanted to get the full block information on the latest block.

.. code-block:: python
  :linenos:

  import asyncio

  # We add BlockTag to our imports, which is an Enumeration for block number special cases such as the "latest" block
  # In this case we use BlockTag.latest to specify the most recent block
  from pythereum import EthRPC, BlockTag

  # pprint helps us print objects in an easy to read manner
  from pprint import pprint

  async def my_first_rpc_connection():
    # If we are using an http or https url, we should include the following argument to EthRPC:
    #   use_socket_pool=False
    async with EthRPC(ENDPOINT_URL) as rpc:
      # We set full_object=True here, as this means transactions in the gotten block will be
      # full transactions, as opposed to transaction hashes
      # Additionally we do not need to use BlockTag objects here,
      # we can instead specify an integer block num if we want.
      block_result = await rpc.get_block_by_number(BlockTag.latest, True)

    # Note the result in this case is of type Block
    # Block objects have all information on a given block, its transactions, etc, conveniently accessible in one object.
    pprint(block_result)

    # We can look at the block's transactions by simply doing:
    pprint(block_result.transactions)

  if __name__ == "__main__":
    asyncio.run(my_first_rpc_connection())

In this case we should get a `Block <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.dclasses.Block>`_
object returned from our `get_block_by_number <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.rpc.EthRPC.get_block_by_number>`_ call,
which contains block information in a convenient container.



So far we have been doing things that Web3.py can do relatively simply, let's move on to something that Pythereum introduces:

Batch RPC calls
===============

Instead of getting block information on just the most recent block, let's get info on 10 blocks, using only one call!

.. code-block:: python
  :linenos:

  import asyncio
  from pythereum import EthRPC, BlockTag
  from pprint import pprint

  async def my_first_rpc_connection():
    # If we are using an http or https url, we should include the following argument to EthRPC:
    #   use_socket_pool=False
    async with EthRPC(ENDPOINT_URL) as rpc:
      # The syntax for batch calls is lists of each parameter of length k in place of normal individual params.
      # list of block numbers to get
      blocks_to_get = [i + 1_000_000 for i in range(10)]
      # For each block number, specify whether full transactions should be gotten
      full_obj_array = [True for i in range(10)]
      block_result = await rpc.get_block_by_number(blocks_to_get, full_obj_array)

    for block in block_result:
      pprint(block)

  if __name__ == "__main__":
    asyncio.run(my_first_rpc_connection())

With only one RPC call, we have successfully gotten 10 times the data,
this helps reduce transmission wait times and lowers demand on your RPC endpoint.
This potentially saves you money if you are on a paid endpoint!

This batch calling syntax we have used here is valid for any EthRPC function that takes parameters.
(i.e. not get_block_number. There is no reason to batch functions of this type as the same data will be returned for each call)

Taking advantage of Websocket Pooling
=====================================

So far we have not been taking advantage of Pythereum's websocket pool.
This pool is here to provide a massive speedup over Web3.py and other Ethereum RPC libraries.

The pool is stored as an asynchronous queue of connections to your endpoint, each of which can communicate with it at the same time.

Pythereum uses this to essentially parallelize your calls for you by taking advantage of asyncio.

Let's see how we would take advantage of multiple sockets to send multiple remote procedure calls at once.

.. code-block:: python
  :linenos:

  import asyncio

  # We add BlockTag to our imports, which is an Enumeration specifying special inputs for get_block_by_number
  # In this case we use BlockTag.latest to specify the most recent block
  from pythereum import EthRPC, BlockTag

  # pprint helps us print objects in an easy to read manner
  from pprint import pprint

  async def my_first_rpc_connection():
    # Since we have used pool_size=3, we can send up to 3 concurrent messages at a given timae
    # Higher pool sizes will mean more concurrent data can be sent at the cost of more instability in connections
    # (Connections which have not been interacted with in a long time may automatically close)
    async with EthRPC(ENDPOINT_URL, pool_size=3) as rpc:
      # We use an asyncio task group to run all of these tasks and collect their results concurrently
      async with asyncio.TaskGroup() as tg:
        # Managed by socket 1
        block_result = tg.create_task(rpc.get_block_by_number(BlockTag.latest, True))
        # Managed by socket 2
        tx_count = tg.create_task(rpc.get_transaction_count_by_number(BlockTag.latest, True))
        # Managed by socket 3
        current_gas_price = tg.create_task(rpc.get_gas_price())

    # Getting all this takes as long as the longest of the operations in your TaskGroup
    pprint(block_result)
    print(tx_count)
    print(current_gas_price)

  if __name__ == "__main__":
    asyncio.run(my_first_rpc_connection())

This provides a speedup of up to n times where n is:

* min(number of functions you are calling, number of sockets in the pool)

This running multiple remote procedure calls at once can also be done using asyncio.gather as follows:

.. code-block:: python
  :linenos:

  res = await asyncio.gather(
    rpc.get_block_by_number(BlockTag.latest, True),
    rpc.get_transaction_count_by_number(BlockTag.latest, True),
    rpc.get_gas_price()
  )

Let's take a look at another useful thing Pythereum introduces.

Subscriptions
=============

Most modern Ethereum nodes support connections via websockets along which a "subscription" can be made.

These subscriptions will continuously output data as it becomes available, such as the headers of all new blocks that are created.

Here is a brief example of how to create a continuous subscription:

.. code-block:: python
  :linenos:

  import asyncio
  from pythereum import EthRPC, SubscriptionType
  from pprint import pprint

  async def my_first_subscription():
    async with EthRPC(ENDPOINT_URL, pool_size=1) as rpc:
      # Declare a subscription to constantly receive data about new block headers
      async with rpc.subscribe(SubscriptionType.new_heads) as sc:
        # Whenever new headers are created this loop will receive the result
        async for header in sc.recv():
          pprint(header)

  if __name__ == "__main__":
    asyncio.run(my_first_subscription())

This is useful for getting live data on the goings-on of transactions on the chain.
This has particular applications in automated traders paying attention to market data, or for getting the right prices to pay for gas.

A brief example of a subscription in use is available in the `demo folder. <https://github.com/gabedonnan/pythereum/blob/main/demo/listen_blocks.py>`_

Transactions
============

One primary use of the blockchain is sending transactions between accounts, with data and amounts of eth attached.

With Pythereum this is made as simple as possible, especially when combined with the eth_account library.
We use transactions as defined in EIP-1559, for the greatest level of efficiency.

.. code-block:: python
  :linenos:

  import asyncio
  from eth_account import Account
  from pythereum import EthRPC, Transaction

  async def my_first_transaction():
    # Create an arbitrary account wallet
    acct = Account.create()
    # Create an arbitrary transaction (most likely will not work, simply an example of fields a transaction has)
    tx = Transaction(
        from_address=acct.address,
        to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
        value=1,
        chain_id=1,
        nonce=1,
        max_fee_per_gas=1
        gas=1
        max_priority_fee_per_gas=1
    )

    signed_tx = acct.sign_transaction(tx).rawTransaction

    async with EthRPC(ENDPOINT_URL, pool_size=1) as rpc:
      await rpc.send_raw_transaction(signed_tx)

  if __name__ == "__main__":
    asyncio.run(my_first_transaction())

This creation of transactions is all well and good but it would be great if we could automate some of it.

With Pythereum's `NonceManager <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.rpc.NonceManager>`_ and `GasManager <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.gas_managers.GasManager>`_ classes that can be done very simply, and with a high degree of control!

Smart Contract / ABI Interaction
--------------------------------

Some transactions require data sent with them, for example if we are interacting with a smart contract, we need to specify what methods we would like to work with, etc.
The methods a smart contract has available are shown in it's ABI, with information on data types for each parameter and returns.
In order to call these methods we must appropriately encode our data to send such that it abides by the ABI's rules.

For example if we are interacting with a method "buyShares(uint256 number, uint256 price)", we need to do a couple things:

* Prepare a number of shares we would like to buy n at price p

* Extract a four byte function selector (this is a four byte value which represents the function to call)

  * This is done by taking the function name we want to call without variable names or spaces like "buyShares(uint256,uint256)"

  * We then call "eth_utils.function_signature_to_4byte_selector" on it, giving us the first four bytes of our data.

* Encode the data we would like to pass as parameters to the function (n and p)

  * We use "eth_abi.encode(["uint256", "uint256"], [n, p])" here, to encode our data to the correct data types

* We then concatenate the selector with the encoded data and voila, we have a complete smart contract function call to pass alongside our transaction

While the end goal is for Pythereum to be able to encode and decode ABI data by itself,
in its current state we can use eth_utils and eth_abi to help us out in development.

.. code-block:: python
  :linenos:

  from eth_utils import function_signature_to_4byte_selector
  from eth_abi import encode

  ...  # Generic RPC setup code inside a class

  async def send_buy_transaction(self, quantity: int, price: int):
    # Get signature and convert it to hexadecimal
    signature = function_signature_to_4byte_selector("buyShares(uint256,uint256)").hex()
    # Get encoded function parameters and convert it to hexadecimal
    encoded_params = encode(["uint256", "uint256"], [quantity, price]).hex()
    # Combine signature and params for final data to send
    final_data = f"0x{signature}{encoded_params}"

    tx = Transaction(
      from_address=self.acct.address,  # My address
      to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",  # Smart contract address
      value=1,  # Value to send alongside data (maybe to pay for shares)
      chain_id=1,
      data=final_data  # Smart contract call data
    )

    # These managers are covered in the next section of the tutorial!
    async with NonceManager(self.rpc) as nm:
      await nm.fill_transaction(tx)
    async with self.gm.informed_manager() as im:
      im.fill_transaction(tx)

    signed_tx = self.acct.sign_transaction(tx).rawTransaction.hex()

    await self.rpc.send_raw_transaction(signed_tx)

Gas and Nonce Management
========================

Let's improve our previous transaction by automatically managing values!

.. code-block:: python
  :linenos:

  import asyncio
  from eth_account import Account
  from pythereum import EthRPC, Transaction, GasManager, NonceManager

  async def my_first_transaction():
    # Create an arbitrary account wallet
    acct = Account.create()
    # Create an arbitrary transaction (most likely will not work, simply an example of fields a transaction has)
    tx = Transaction(
        from_address=acct.address,
        to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
        value=1,
        chain_id=1,
    )

    manager_rpc = EthRPC(ENDPOINT_URL, pool_size=2)

    # Manually start the pool of our manager RPC for use in our gas and nonce managers
    await manager_rpc.start_pool()

    # Gas and Nonce managers need an RPC connection to get block context information
    gm = GasManager(manager_rpc)

    # Gas managers have multiple possible strategies, we will simply be using naive managers here
    # Fills gas, max_fee_per_gas, max_priority_fee_per_gas values in the transaction
    # This is done by taking the average of those values from the previous block (though different strategies can be specified)
    async with gm.naive_manager() as nvm:
      await nvm.fill_transaction(tx)

    # Gets the nonce of the given account, for new accounts this will be 0
    async with NonceManager(manager_rpc) as nm:
      await nm.fill_transaction(tx)

    signed_tx = acct.sign_transaction(tx).rawTransaction

    await manager_rpc.send_raw_transaction(signed_tx)

    # The pool should be closed at the end when EthRPC not used in an "async with" statement
    await manager_rpc.close_pool()

  if __name__ == "__main__":
    asyncio.run(my_first_transaction())

Now we can automatically fill our transactions without having to calculate these values ourselves!

Gas Managers
------------

Currently, there are two types of GasManager, the `informed_manager <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.gas_managers.GasManager.informed_manager>`_
and the `naive_manager. <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.gas_managers.GasManager.naive_manager>`_

The naive gas manager fills transactions using strategies from a given `GasStrategy <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.common.GasStrategy>`_
object or dictionary of GasStrategy objects.

The available strategies are as follows:

* mean_price - Price is filled with mean of previous block prices
* median_price - Price filled with median of previous block prices
* mode_price - Price filled with modal value of previous block prices
* max_price - Price filled with max price of previous block
* min_price - Price filled with min price of previous block
* upper_quartile_price - Price filled with upper quartile value of previous block
* lower_quartile_price - Price filled with lower quartile value of previous block

We can use either one global strategy for all 3 gas price values (gas, maxFeePerGas, maxPriorityFeePerGas)
or we can use separate strategies.

The syntax is as follows:

.. code-block:: python
  :linenos:

  # With single strategy
  async with gm.naive_manager() as nvm:
    await nvm.fill_transaction(tx, strategy=GasStrategy.lower_quartile_price)

  # With separate strategies
  strategy_dict = {
    "gas": GasStrategy.max_price,
    "maxFeePerGas": GasStrategy.lower_quartile_price,
    "maxPriorityFeePerGas": GasStrategy.mean_price,
  }
  async with gm.naive_manager() as nvm:
    await nvm.fill_transaction(tx, strategy=strategy_dict)

As is evident from the name, this gas management strategy is naive, not learning from previous transactions.

If we want to price our gas based on previous transaction results, we should instead use informed_manager.

Pricing gas in this way is important in long term operation where many transactions are made.
This is because when a transaction succeeds we can lower our gas prices to save eth,
and when a transaction fails we can up gas prices to ensure execution.

Below is an example of how an informed manager is used.

.. code-block:: python
  :linenos:

  # Generic setup code similar to before
  ...

  # Fill our transaction with initial values in similar way to naive manager
  async with gm.informed_manager() as im:
    im.fill_transaction(tx)

  # Sign and submit our transaction
  signed_tx = acct.sign_transaction(tx).rawTransaction
  tx_hash = await manager_rpc.send_raw_transaction(signed_tx)

  # Find out whether transaction succeeded by getting transaction receipt
  tx_result = await manager_rpc.get_transaction_receipt(tx_hash, retries=3)

  # Open up our informed manager again, this time with a success multiplier and failure multiplier
  async with gm.informed_manager(
    success_multiplier=0.9,
    fail_multiplier=1.3
  ) as im:
    if tx_result.status == 0:
      # Tell the gas manager that the execution failed
      # This way next time the price of maxPriorityFeePerGas will be multiplied by the fail multiplier
      # This should help guarantee success of execution
      # If this does not work the tx may have failed because gas was too low, in which case use im.gas_fail()
      im.execution_fail()
    else:
      # Lowers priority fee by success multiplier such that next time transactions may be cheaper
      im.execution_success()

  # The next time we need to fill a transaction using this same gas manager instance
  # The informed manager will have adjusted prices accordingly

These gas management types both have their own use cases, and it is up to the user which one suits them best.

The Nonce Manager
-----------------

The nonce manager works somewhat differently to GasManager objects in that there are no NonceManager sub strategies.

The nonce manager gets the number of transactions an account has sent, and uses that to determine the current nonce to apply to a transaction to send.

The syntax for this is visible in earlier examples.

A brief more complete example of nonce and gas management in use is available in the `demo folder <https://github.com/gabedonnan/pythereum/blob/main/demo/block_submissions.py>`_

Block Builder Submission
========================

This area of the tutorial is for more advanced users who know what they are doing with block builders and submissions.
The library is additionally still under-tested in some areas related to block submission, any feedback here is always welcome.

If this is not you, do not worry, this is simply a section to cater to more advanced users, simply continue to the next section.

When transactions are sent out for execution, they are stored in a public memory pool (mempool).

Other users can read information in this mempool and act on the information in there.
(maybe you are trying to buy a friendtech share and someone outbids you after seeing your bid in the memory pool, causing you to lose out)

As such, submitting your transactions to a `Block Builder <https://ethereum.org/nl/roadmap/pbs/>`_
directly without them floating around in the mempool may be desirable.

Pythereum introduces the `BuilderRPC <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.builders.BuilderRPC>`_ class to facilitate this.

Since most block builders do not support websocket connection, this BuilderRPC class communicates over HTTP using aiohttp.

There are many block builders, each of which compete to create the next block,
as such in order to have the best likelihood for your transaction to be included in the final minted block,
it is advisable to submit to many of them at once.

Here is an example of block builder submission to the TitanBuilder and Builder0x69.
A snapshot of the most popular block builders can be found at `mevboost.pics <https://mevboost.pics/>`_

.. code-block:: python
  :linenos:

  import asyncio
  from pythereum import (
    Transaction, EthRPC, GasManager, NonceManager,
    BuilderRPC, TitanBuilder, Builder0x69, HexStr,
  )
  from eth_account import Account

  async def my_first_builder_submission():
    acct = Account.create()
      # Create an arbitrary transaction (minus gas and nonce values)
    tx = Transaction(
        from_address=acct.address,
        to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
        value=1,
        chain_id=1,
    )

    manager_rpc = EthRPC(erpc_url, 2)
    gm = GasManager(manager_rpc)
    await manager_rpc.start_pool()

    async with NonceManager(manager_rpc) as nm:
      await nm.fill_transaction(tx)

    async with gm.naive_manager() as nvm:
      await nvm.fill_transaction(tx)

    signed_tx = acct.sign_transaction(tx).rawTransaction

    # A list of block builders to submit to is used, in this case TitanBuilder and Builder0x69
    # Pythereum comes with inbuilt support for many of the most popular block builders
    # Support for more can be added by inheriting from Pythereum's Builder base class
    # We pass in the private key of our account to the builder RPC to sign payloads with flashbots headers (not always relevant but sometiems necessary)
    async with BuilderRPC(
      [TitanBuilder(), Builder0x69()], private_key=acct.key
    ) as brpc:
      msg = await brpc.send_private_transaction(HexStr(signed_tx))

    print(msg)
    await manager_rpc.close_pool()

  if __name__ == "__main__":
    asyncio.run(my_first_builder_submission())

This is very similar to an example in the demo folder,

In addition to single transactions, there exists support for Bundle submissions (which are the private transaction equivalent to batch sending transactions),
and mevboost bundles (a new transaction protocol popularised by the flashbots builder).

Examples below:

.. code-block:: python
  :linenos:

  # Bundle submission

  # Bundles have a large amount of optional parameters
  # Check your chosen block builder's documentation for more info (e.g. https://docs.titanbuilder.xyz/api/eth_sendbundle)
  bd = Bundle(
    txs=[tx for tx in signed_transactions],
  )

  async with BuilderRPC(
    [TitanBuilder()], private_key=acct.key
  ) as brpc:
    msg = await brpc.send_bundle(bd)

  print(msg)

.. code-block:: python
  :linenos:

  # MEVBundle submission

  # MEVBundles have a large amount of optional parameters, similar to normal bundles,
  # Check Pythereum's implementation and flashbots documentation for info
  bd = MEVBundle(
    block=(await rpc.get_block_number()) + 1,  # The bundle is valid for the next block
    refund_addresses=["0x5fC2E691E520bbd3499f409bb9602DBA94184672"],
    refund_percentages=[100],
  )

  async with BuilderRPC(
    [FlashbotsBuilder()], private_key=acct.key
  ) as brpc:
    msg = await brpc.send_mev_bundle(bd)

  print(msg)

Mempool Access
==============

The memory pool (mempool) holds proposed transactions in a public place before they are either added to a block or discarded.

Accessing the possible transactions that others may make in the future is an important way to gain an advantage when interacting with the Ethereum blockchain.

The way to access this mempool is different depending on what type of node you are connected to,
for geth or OpenEthereum parity nodes there are inbuilt methods for this.

.. code-block:: python
  :linenos:

  await rpc.get_mempool_geth()
  await rpc.get_mempool_parity()

However if you are connected to another ethereum endpoint type there may not be a simple method to do this.
Instead it is possible to use subscriptions to build up your own picture of the mempool using the new pending transactions subscription type.

