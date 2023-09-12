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
- Private transaction and Bundle support for communication directly with block builders

### Implemented RPC methods

All methods listed in the [Ethereum JSON RPC API specification](https://ethereum.org/en/developers/docs/apis/json-rpc/) are completed as of version `1.0.5`, 
alongside methods for subscriptions, and support for calling custom function names with custom parameters.

### Supported Builders

With the `BuilderRPC` class, pythereum supports submitting bundles and private transactions directly to block builders.
Each builder class that can be passed into BuilderRPC instances automatically manages communication with the given builder.

The following builder classes are currently implemented:

- Titan Builder
- Rsync Builder
- Beaver Builder (Using same parameters as rsync, may need adjustment)
- Builder0x69
- Flashbots Builder (additional robustness testing needed)

With support for creating custom builder classes by inheriting from the `Builder` class.
An implementation of the Beaver Builder and support for [mevboost](mevboost.pics) coming in future versions.

### Example usage

#### Basic single function call

```python
# Example simple function
import asyncio
from pythereum import EthRPC

TEST_URL = "ws://127.0.0.1:8545"

async def test_transaction_count():
  async with EthRPC(TEST_URL, pool_size=1) as erpc:
    # Gets the number of transactions sent from a given EOA address
    r = await erpc.get_transaction_count("0xabcdefghijklmnopqrstuvwxyz1234567890")
    print(r)

if __name__ == "__main__":
  asyncio.run(test_transaction_count())
```

#### Example subscription

```python
# Example subscription
import asyncio
from pythereum import EthRPC, SubscriptionType

TEST_URL = "ws://127.0.0.1:8545"

async def test_subscription(subscription_type: SubscriptionType):
  """
  Creates a subscription to receive data about all new heads
  Prints each new subscription result as it is received
  """
  async with EthRPC(TEST_URL, pool_size=1) as erpc:
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
from pythereum import EthRPC

TEST_URL = "ws://127.0.0.1:8545"

async def test_batching():
  # Batch calls can be applied to any parameterised method
  # Each parameter must be passed in as a list 
  # With list length k where k is the batch size
  async with EthRPC(TEST_URL, pool_size=1) as erpc:
    r = await erpc.get_block_by_number(
      block_specifier=[
        i for i in range(40000, 40010)
      ],
      full_object=[
        True for _ in range(10)
      ]
    )
    print(r)


if __name__ == "__main__":
  asyncio.run(test_batching())
```

#### Example currency conversion

```python
>>> from pythereum import EthDenomination, convert_eth
>>> convert_eth(1_000_000, convert_from=EthDenomination.wei, covert_to=EthDenomination.ether)
1e-12
>>> convert_eth(1_000, EthDenomination.babbage, EthDenomination.finney)
1e-09
```

#### Example builder submission

```python
# Example builder submission
import asyncio
from eth_account import Account
from pythereum import BuilderRPC, TitanBuilder


async def test_building():
  # Create new arbitrary account wallet
  acct = Account.create()
  # Create an arbitrary transaction
  tx = {
    "from": f"{acct.address}",
    "to": "0x5fC2E691E520bbd3499f409bb9602DBA94184672",
    "value": 1,
    "gas": 2000000,
    "gasPrice": 234567897654321,
    "nonce": 0,
    "chainId": 1
  }
  
  # Sign your transaction with your account's key
  signed_tx = Account.sign_transaction(tx, acct.key)
  
  async with BuilderRPC(TitanBuilder()) as brpc:
    msg = await brpc.send_private_transaction(signed_tx)
    print(msg)


if __name__ == "__main__":
  asyncio.run(test_building())
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
pythereum = "^1.1.0"
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
