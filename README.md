# eth_rpc
A lightweight alternative to Web3.py in development

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
- Methods to implement
  - [ ] `eth_getStorageAt`
  - [ ] `eth_getTransactionCountByHash`
  - [ ] `eth_getTransactionCountByNumber`
  - [ ] `eth_getUncleCountByBlockHash`
  - [ ] `eth_getUncleCountByBlockNumber`
  - etc.


- [ ] Add websocket pool
- [ ] Enhance tests

```python
# Example usage
import asyncio
from eth_rpc import EthRPC

TEST_URL = "http://127.0.0.1:8545"
erpc = EthRPC(TEST_URL)

async def test_transaction_count(self):
    # Prints the transaction count for a given address
    r = await erpc.get_transaction_count("0xabcdefghijklmnopqrstuvwxyz1234567890")
    print(r)

asyncio.run(test_transaction_count())
```

# Getting started

Install foundry
