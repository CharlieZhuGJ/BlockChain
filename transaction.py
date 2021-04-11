import json
import hashlib
from datetime import datetime
# 导入椭圆曲线算法
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError
import binascii
import base64
from hashlib import sha256


class Wallet:
    """
        钱包
    """
    def __init__(self):
        """
            钱包初始化时基于椭圆曲线生成一个唯一的秘钥对，代表区块链上一个唯一的账户
        """
        self._private_key = SigningKey.generate(curve=SECP256k1)
        self._public_key = self._private_key.get_verifying_key()

    @property
    def address(self):
        """
            这里通过公钥生成地址
        """
        h = sha256(self._public_key.to_pem())
        return base64.b64encode(h.digest())

    @property
    def pubkey(self):
        """
            返回公钥字符串
        """
        return self._public_key.to_pem()

    def sign(self, message):
        """
            生成数字签名
        """
        h = sha256(message.encode('utf8'))
        return binascii.hexlify(self._private_key.sign(h.digest()))

def verify_sign(pubkey, message, signature):
    """
        验证签名
    """
    verifier = VerifyingKey.from_pem(pubkey)
    h = sha256(message.encode('utf8'))
    return verifier.verify(binascii.unhexlify(signature), h.digest())


class Transaction(object):
    def __init__(self, sender, recipient, amount):
        if isinstance(sender, bytes):
            sender = sender.decode('utf-8')
        self.sender = sender

        if isinstance(recipient, bytes):
            recipient = recipient.decode('utf-8')
        self.recipient = recipient
        self.amount = amount

    def set_sign(self, signature, pubkey):
        self.signature = signature
        self.pubkey = pubkey

    def __repr__(self):
        if self.sender:
            s = "从%s转至%s %d个加密货币" % (self.sender, self.recipient, self.amount)
        else:
            s = "从%s 挖矿获取%d个加密货币" % (self.recipient, self.amount)
        return s


class TransactionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Transaction):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(self, obj)


class Block(object):
    def __init__(self, transactions, prev_hash):
        self.prev_hash = prev_hash
        self.transactions = transactions
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.nonce = None
        self.hash = None

    def __repr__(self):
        return "区块内容：%s\n哈希值：%s" % (json.dumps(self.transactions), self.hash)


class ProofOfWork(object):
    def __init__(self, block, miner, difficult=5):
        self.block = block
        self.difficulty = difficult
        self.reward_amount = 1
        self.miner = miner

    def message(self):
        message = hashlib.sha256()
        message.update(str(self.block.prev_hash).encode('utf-8'))
        message.update(str(self.block.data).encode('utf-8'))
        message.update(str(self.block.timestamp).encode('utf-8'))
        return message

    def mine(self):
        i = 0
        prefix = '0' * self.difficulty

        t = Transaction(sender="", recipient=self.miner.address, amount=self.reward_amount)
        sig = self.miner.sign(json.dumps(t, cls=TransactionEncoder))
        t.set_sign(sig, self.miner.pubkey)
        self.block.transactions.append(t)


        while True:
            message = hashlib.sha256()
            message.update(str(self.block.prev_hash).encode('utf-8'))
            # 更新区块中的交易数据
            # message.update(str(self.block.data).encode('utf-8'))
            message.update(str(self.block.transactions).encode('utf-8'))
            message.update(str(self.block.timestamp).encode('utf-8'))
            message.update(str(i).encode("utf-8"))
            digest = message.hexdigest()
            if digest.startswith(prefix):
                self.block.nonce = i
                self.block.hash = digest
                return self.block
            i += 1

    def validate(self):
        """
            验证有效性
        """
        message = hashlib.sha256()
        message.update(str(self.block.prev_hash).encode('utf-8'))
        # 更新区块中的交易数据
        # message.update(str(self.block.data).encode('utf-8'))
        message.update(json.dumps(self.block.transactions).encode('utf-8'))
        message.update(str(self.block.timestamp).encode('utf-8'))
        message.update(str(self.block.nonce).encode('utf-8'))
        digest = message.hexdigest()

        prefix = '0' * self.difficulty
        return digest.startswith(prefix)


class BlockChain:
    """
        区块链结构体
        blocks: 包含的区块列表
    """

    def __init__(self):
        self.blocks = []

    def add_block(self, block):
        """
        添加区块
        """
        self.blocks.append(block)

    def print_list(self):
        print("区块链包含区块个数: %d\n" % len(self.blocks))
        for block in self.blocks:
            print("上个区块哈希：%s" % block.prev_hash)
            print("区块内容：%s" % block.transactions)
            print("区块哈希：%s" % block.hash)
            print("\n")

def get_balance(user):
    balance = 0
    for block in blockchain.blocks:
        for t in block.transactions:
            if t.sender == user.address.decode():
                balance -= t.amount
            elif t.recipient == user.address.decode():
                balance += t.amount
    return balance


# 初始化区块链
blockchain = BlockChain()

# 创建三个钱包，一个属于alice，一个属于tom，剩下一个属于bob
alice = Wallet()
tom = Wallet()
bob = Wallet()

# 打印当前钱包情况
print("alice: %d个加密货币" % (get_balance(alice)))
print("tom: %d个加密货币" % (get_balance(tom)))
print("bob: %d个加密货币" % (get_balance(bob)))

# alice生成创世区块，并添加到区块链中

new_block1 = Block(transactions=[], prev_hash="")
w1 = ProofOfWork(new_block1, alice)
genesis_block = w1.mine()
blockchain.add_block(genesis_block)
# 显示alice当前余额

print("alice: %d个加密货币" % (get_balance(alice)))


# alice 转账给 tom 0.3个加密货币
transactions = []
new_transaction = Transaction(
    sender=alice.address,
    recipient=tom.address,
    amount=0.3
)
sig = tom.sign(str(new_transaction))
new_transaction.set_sign(sig, tom.pubkey)

# bob 在网络上接收到这笔交易，进行验证没问题后生成一个新的区块并添加到区块链中

if verify_sign(new_transaction.pubkey,
               str(new_transaction),
               new_transaction.signature):

    # 验证交易签名没问题，生成一个新的区块
    print("验证交易成功")
    new_block2 = Block(transactions=[new_transaction], prev_hash="")
    print("生成新的区块...")
    w2 = ProofOfWork(new_block2, bob)
    block = w2.mine()
    print("将新区块添加到区块链中")
    blockchain.add_block(block)
else:
    print("交易验证失败！")

# 打印当前钱包情况
print("alice: %.1f个加密货币" % (get_balance(alice)))
print("tom: %.1f个加密货币" % (get_balance(tom)))
print("bob: %d个加密货币" % (get_balance(bob)))









