Welcome to Pythereum's tutorial
===============================

Getting started
---------------

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

"async with EthRPC(ENDPOINT_URL) as rpc:"

This line starts up a pool of websockets to connect to the given endpoint, when we exit the scope of
"async with", the connection pool is automatically closed.

Any function we call using the "rpc" object we create will use the pool of websockets here to communicate with our endpoint.

* We use our connection to call "get_block_number"

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
      block_result = await rpc.get_block_by_number(BlockTag.latest, True)

    # Note the result in this case is of type Block
    # Block objects have all information on a given block, its transactions, etc, conveniently accessible in one object.
    pprint(block_result)

  if __name__ == "__main__":
    asyncio.run(my_first_rpc_connection())

In this case we should get a `Block <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.dclasses.Block>`_
object returned from our `get_block_by_number <https://pythereum.readthedocs.io/en/latest/pythereum.html#pythereum.rpc.EthRPC.get_block_by_number>`_ call,
which contains block information in a convenient container.