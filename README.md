# pythereum
(formerly eth_rpc)
### A lightweight Ethereum RPC library for Python

Features include:
- Ability to initiate remote procedure calls on a wide variety of ethereum functions
- Websocket pooling for high performance calls
- Support for RPC batching, allowing multiple calls to the same function at once
- "eth_subscribe" functionality
- Currency conversion, with support for esoteric denomination names (e.g. lovelace)
- Private transaction and Bundle support for communication directly with block builders
- Automatic nonce and gas management for transactions
- Typed function outputs for intuitive library use


### Implemented RPC methods

All methods listed in the [Ethereum JSON RPC API specification](https://ethereum.org/en/developers/docs/apis/json-rpc/) are completed as of version `1.0.5`,
alongside methods for subscriptions, and support for calling custom function names with custom parameters.

### Supported Builders

With the `BuilderRPC` class, pythereum supports submitting bundles and private transactions directly to block builders.
Each builder class that can be passed into BuilderRPC instances automatically manages communication with the given builder.

The following builder classes are currently implemented:

- Titan Builder
- Rsync Builder
- Builder0x69
- Flashbots Builder
- Beaver Builder (Very poorly documented parameters online, may need adjustment)


Each of these now have support for [mevboost](https://mevboost.pics) bundles.

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
    r = await erpc.get_transaction_count("0x5fC2E691E520bbd3499f409bb9602DBA94184672")
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
from pythereum import BuilderRPC, TitanBuilder, HexStr, Transaction


async def test_builder_submission():
  # Create new arbitrary account wallet
  acct = Account.create()
  # Create an arbitrary EIP-1559 transaction
  # This transaction is an equivalence to a dictionary, 
  # it simply provides a convenient constructor
  tx = Transaction(
    from_address=acct.address,
    to_address="0x5fC2E691E520bbd3499f409bb9602DBA94184672",
    value=1,
    max_priority_fee_per_gas=1,
    max_fee_per_gas=1,
    gas=1,
    chain_id=1,
    nonce=0
  )

  # Sign your transaction with your account's key
  signed_tx = Account.sign_transaction(tx, acct.key).rawTransaction

  async with BuilderRPC(TitanBuilder()) as brpc:
    msg = await brpc.send_private_transaction(HexStr(signed_tx))
    print(msg)


if __name__ == "__main__":
  asyncio.run(test_builder_submission())
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
The library currently requires python versions `>=3.11`.

If you want to include this library for use in another project via Poetry
you must simply add the following to your `pyproject.toml` file under `[tool.poetry.dependencies]`

```toml
pythereum = {git = "https://github.com/gabedonnan/pythereum.git"}
```

or

```toml
pythereum = "^1.1.4"
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

```bash
anvil rpc-url EXAMPLE_RPC_URL@EXAMPLE_BLOCK_NUM
```

This is helpful for ensuring consistency in tests, or to simply have a simulated RPC client, run:

```bash
anvil
```

### Acknowledgements

Special thanks to [@totlsota](https://github.com/totlsota) as a more experienced blockchain developer than I, for giving me pointers when I needed them and
generally assisting in the development of this project.
