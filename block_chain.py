import time
import hashlib
import base64
from ecdsa import SigningKey, SECP256k1
# import matplotlib.pyplot as plt
from datetime import datetime


class Block(object):
    def __init__(self, data, prev_hash):
        self.prev_hash = prev_hash
        self.data = data
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = hashlib.sha256()
        message.update(str(self.prev_hash).encode('utf-8'))
        message.update(str(self.data).encode('utf-8'))
        message.update(str(self.timestamp).encode('utf-8'))

        self.hash = message.hexdigest()

        self.nonce = None


class BlockChain(object):
    def __init__(self):
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)


genesis_block = Block("创世区块", "")
print(genesis_block.hash)
blcok2 = Block("第二块", genesis_block.hash)
print(blcok2.hash)
blcok3 = Block("第三块", blcok2.hash)
print(blcok3.hash)


block_chain = BlockChain()
block_chain.add_block(genesis_block)
block_chain.add_block(blcok2)
block_chain.add_block(blcok3)

for block_ in block_chain.blocks:
    print(block_.prev_hash)
    print(block_.data)
    print(block_.hash)



