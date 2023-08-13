# eth_rpc
### A lightweight Ethereum RPC library for Python in development

Features include:
- Ability to initiate RPC calls on a wide variety of ethereum functions
  - More functions are added whenever possible to this list
- Custom data types for easy manipulation of RPC results
- Eth_subscribe functionality
- Websocket pooling for high performance calls
- Future support for RPC batching

### Documentation of progress below (wil add more as I go!)

- [x] Implement websocket instead of HTTP
- [x] Implemented methods
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
- Methods to implement
  - [ ] `eth_getStorageAt`
  - [ ] `eth_getTransactionCountByHash`
  - [ ] `eth_getTransactionCountByNumber`
  - [ ] `eth_getUncleCountByBlockHash`
  - [ ] `eth_getUncleCountByBlockNumber`
  - etc., aiming to complete all methods listed [here.](https://ethereum.org/en/developers/docs/apis/json-rpc/)


- [x] Add websocket pool
  - [x] Basic pooling functionality added
  - [ ] Optimisation and improving pooling
- [ ] Implement batch procedure calls
- [ ] Enhance tests
- [x] Add custom typing
  - [x] Add Hex type
  - [x] Add Binary type
  - [ ] Expand custom typing functionality

```python
# Example usage
import asyncio
from eth_rpc import EthRPC

TEST_URL = "http://127.0.0.1:8545"
erpc = EthRPC(TEST_URL, pool_size=10)
# Optional step to start your thread pool before your first function call
asyncio.run(erpc.start_pool())

async def test_transaction_count():
    # Gets the number of transactions sent from a given EOA address
    r = await erpc.get_transaction_count("0xabcdefghijklmnopqrstuvwxyz1234567890")
    print(r)

asyncio.run(test_transaction_count())
```

```python
# Example subscription

async def test_subscription(subscription_type: SubscriptionEnum):
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

asyncio.run(test_subscription(SubscriptionEnum.new_heads))
```

# Getting started

## Testing your programs

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
