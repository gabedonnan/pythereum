Tutorial
========

The Basics
----------

At it's core Pythereum provides functionality to interact efficiently with Ethereum nodes via the Ethereum JSON RPC API.

In order to get started we need an `Ethereum endpoint <https://ethereum.org/en/developers/docs/nodes-and-clients/>`_ to connect to, for which you will need a connection URL.
This URL can use the following prefixes for fast websocketed functionality:

* wss://
* ws://

For http connection you can also use:

* https://
* http://

For this tutorial I will be using a personal node I connect to which will be referred to as "ENDPOINT_URL".

Much of Pythereum's functionality is asynchronous, which means we will need the library asyncio to run our code.

For our first block of code let's try and get the number of the most recent block.

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

  # We add BlockTag to our imports, which is an Enumeration specifying special inputs for get_block_by_number
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
---------------

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
-------------------------------------

So far we have not been taking advantage of Pythereum's websocket pool.
This pool is here to provide a massive speedup over Web3.py and other Ethereum RPC libraries.

The pool is stored as an asynchronous queue of connections to your endpoint, each of which can communicate with it at the same time.

This essentially parallelizes your calls for you by taking advantage of asyncio.

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

