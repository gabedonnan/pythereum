# pythereum 
(formerly eth_rpc)
### A lightweight Ethereum RPC library for Python

Features include:
- Ability to initiate remote procedure calls on a wide variety of ethereum functions
  - More functions are added whenever possible to this list
- Typed function outputs for easy manipulation of results
- "eth_subscribe" functionality
- Websocket pooling for high performance calls
- Support for RPC batching, allowing multiple calls to the same function at once
- Currency conversion for wei, so you don't have to rely on external libs like Web3.py

### Implemented RPC methods

  - [x] `eth_blockNumber`
  - [x] `eth_getTransactionCount`
  - [x] `eth_getBalance`
  - [x] `eth_gasPrice`
  - [x] `eth_getBlockByNumber`
  - [x] `eth_getblockByHash`
  - [x] `eth_call`
  - [x] `eth_getTransactionReceipt`
  - [x] `eth_sendRawTransaction`
  - [x] `eth_sendTransaction`
  - [x] `eth_syncing`
  - [x] `eth_coinbase`
  - [x] `eth_chainId`
  - [x] `eth_mining`
  - [x] `eth_hashrate`
  - [x] `eth_accounts`
  - [x] `eth_subscribe`
  - [x] `eth_getBlockTransactionCountByHash`
  - [x] `eth_getBlocktransactionCountbyNumber`
  - [x] `eth_getUncleCountByBlockHash`
  - [x] `eth_getUncleCountByBlockNumber`
  - [x] `eth_getCode`
  - [x] `eth_estimateGas`
  - [x] `eth_sign`
  - [x] `eth_getTransactionByHash`
  - [x] `eth_getTransactionByBlockHashAndIndex`
  - [x] `eth_getTransactionByBlockNumberAndIndex`
  - [x] `eth_getUncleByBlockHashAndIndex`
  - [x] `eth_getUncleByBlockNumberAndIndex`
  - [x] `eth_newFilter`
    - Additional testing needed for batching this function
  - [x] `eth_newBlockFilter`
  - [x] `eth_newPendingTransactionFilter`
  - [x] `eth_uninstallFilter`
  - [x] `eth_getFilterLogs`
  - [x] `eth_getFilterChanges
`

RPC methods to implement
  - Aiming to complete all methods listed [here.](https://ethereum.org/en/developers/docs/apis/json-rpc/)



### Example usage

#### Basic single function call

```python
# Example simple function
import asyncio
from pythereum import EthRPC

TEST_URL = "ws://127.0.0.1:8545"
erpc = EthRPC(TEST_URL, pool_size=2)


async def test_transaction_count():
  # Optional step to start your thread pool before your RPC call
  await erpc.start_pool()
  # Gets the number of transactions sent from a given EOA address
  r = await erpc.get_transaction_count("0xabcdefghijklmnopqrstuvwxyz1234567890")
  print(r)
  # Ensures no hanging connections are left
  await erpc.close_pool()


if __name__ == "__main__":
  asyncio.run(test_transaction_count())
```

#### Example subscription

```python
# Example subscription
import asyncio
from pythereum import EthRPC, SubscriptionType

TEST_URL = "ws://127.0.0.1:8545"
erpc = EthRPC(TEST_URL, pool_size=2)


async def test_subscription(subscription_type: SubscriptionType):
  """
  Creates a subscription to receive data about all new heads
  Prints each new subscription result as it is received
  """
  async with erpc.subscribe(subscription_type) as sc:
    # The following will iterate as each item is gotten by sc.recv()
    async for item in sc.recv():
      # 'item' is formatted into the appropriate form for its subscription type
      # this is done by the sc.recv() automatically
      print(item)


if __name__ == "__main__":
  asyncio.run(test_subscription(SubscriptionType.new_heads))
```

#### Example batch call

```python
# Example batch call
import asyncio
from pythereum import EthRPC, BlockTag

TEST_URL = "ws://127.0.0.1:8545"
erpc = EthRPC(TEST_URL, pool_size=2)


async def test_batching():
  await erpc.start_pool()
  # Batch calls can be applied to any parameterised method
  # Each parameter must be passed in as a list 
  # With list length k where k is the batch size
  r = await erpc.get_block_by_number(
    block_specifier=[
      i for i in range(40000, 40010)
    ],
    full_object=[
      True for i in range(10)
    ]
  )
  print(r)
  await erpc.close_pool()


if __name__ == "__main__":
  asyncio.run(test_batching())
```

#### Example currency conversion

```python
>> > from pythereum import EthDenomination, convert_eth
>> > convert_eth(1_000_000, convert_from=EthDenomination.wei, covert_to=EthDenomination.ether)
1e-12
>> > convert_eth(1_000, convert_from=EthDenomination.babbage, covert_to=EthDenomination.finney)
1e-09
```

More examples available in the [demo](https://github.com/gabedonnan/pythereum/tree/main/demo) folder.

# Getting started

## Poetry

This project and its dependencies are managed by python poetry,
which will automatically manage the versions of each library / python version
upon which this project depends.

Install poetry with the instructions [here.](https://python-poetry.org/docs/)

## Installation

### Poetry Installation
The library currently requires python versions `>=3.11,<3.13`.

If you want to include this library for use in another project via Poetry
you must simply add the following to your `pyproject.toml` file under `[tool.poetry.dependencies]`

```toml
pythereum = {git = "https://github.com/gabedonnan/pythereum.git"}
```

or 

```toml
pythereum = "^1.0.2"
```

If you would like to install the library via pypi instead of via this git repository.
This git repository will always be the most up to date but the releases on pypi should
be more thoroughly tested.

### Pip / PyPi installation

The library is now available via pip!! (I had to change the whole project name to get it there)

It can be installed with the following command, or downloaded [here](https://pypi.org/project/pythereum/):

```commandline
python3 -m pip install pythereum
```


## Testing your programs

Testing a program built with this library can be done with actual ethereum
nodes, though they may rate limit you or cost eth to run.
As such using testing programs such as Anvil from the Foundry suite of products
allows for faster and more productive testing.

### Install foundry

Instructions available at [this link.](https://book.getfoundry.sh/getting-started/installation)

### Run anvil

Anvil is a blockchain testing application included with foundry.

The following command will run an instance of anvil representing 
the blockchain's status at block number ```EXAMPLE_BLOCK_NUM``` via url
```EXAMPLE_RPC_URL```.

This is helpful for ensuring consistency in tests.

```bash
anvil rpc-url EXAMPLE_RPC_URL@EXAMPLE_BLOCK_NUM
```

### Acknowledgements

Special thanks to [@totlsota](https://github.com/totlsota) as a more experienced blockchain developer than I, for giving me pointers when I needed them and
generally assisting in the development of this project.
