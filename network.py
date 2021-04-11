import socket
import threading
import pickle
import hashlib
from transaction import Wallet, Transaction, verify_sign, Block, ProofOfWork, BlockChain

# 定义一个全局列表保存所有节点
NODE_LIST = []
DIFFICULTY = 5
PER_BYTE = 15


class Node(threading.Thread):
    def __init__(self, name, port, host="localhost"):
        threading.Thread.__init__(self, name=name)
        self.host = host  # 服务器地址，本地电脑都设为localhost
        self.port = port  # 每个节点对应一个唯一的端口号
        self.name = name  # 唯一的节点名称
        self.wallet = Wallet()
        self.blockchain = BlockChain()  # 用来存储一个区块链副本

    def run(self):
        """
            节点运行
        """
        self.init_blockchain()  # 初始化区块链

        # 在指定端口进行监听
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        NODE_LIST.append({
            "name": self.name,
            "host": self.host,
            "port": self.port
        })
        sock.listen(10)
        print(self.name, "运行中...")
        while True:  # 不断处理其他节点发送的请求
            connection, address = sock.accept()
            try:
                print(self.name, "处理请求内容...")
                self.handle_request(connection)
            except socket.timeout:
                print('超时!')
            except Exception as e:
                print(e, )
            connection.close()

    def handle_request(self, connection):
        data = []
        while True:  # 不断读取请求数据直至读取完成
            buf = connection.recv(PER_BYTE)
            if not buf:  # 若读取不到新的数据则退出
                break
            data.append(buf)
            if len(buf) < PER_BYTE:  # 若读取到的数据长度小于规定长度，说明数据读取完成，退出
                break
        t = pickle.loads(b''.join(data))
        if isinstance(t, Transaction):  # 如果是新区块类型类型消息
            print("处理交易请求...")
            if verify_sign(t.pubkey, str(t), t.signature):

                # 验证交易签名没问题，生成一个新的区块
                print(self.name, "验证交易成功")
                new_block = Block(transactions=[t], prev_hash="")
                print(self.name, "生成新的区块...")
                w = ProofOfWork(new_block, self.wallet)
                block = w.mine()
                print(self.name, "将新区块添加到区块链中")
                self.blockchain.add_block(block)
                print(self.name, "将新区块广播到网络中...")
                self.broadcast_new_block(block)
            else:
                print(self.name, "交易验证失败！")
        elif isinstance(t, Block):
            print("处理新区块请求...")
            if self.verify_block(t):
                print(self.name, "区块验证成功")
                self.blockchain.add_block(t)
                print(self.name, "添加新区块成功")
            else:
                print(self.name, "区块验证失败!")
        else:  # 如果不是新区块消息，默认为初始化消息类型，返回本地区块链内容
            connection.send(pickle.dumps(self.blockchain))

    def verify_block(self, block):
        """
            验证区块有效性
        """
        message = hashlib.sha256()
        message.update(str(block.prev_hash).encode('utf-8'))
        # 更新区块中的交易数据
        # message.update(str(self.block.data).encode('utf-8'))
        message.update(str(block.transactions).encode('utf-8'))
        message.update(str(block.timestamp).encode('utf-8'))
        message.update(str(block.nonce).encode('utf-8'))
        digest = message.hexdigest()

        prefix = '0' * DIFFICULTY
        return digest.startswith(prefix)

    def broadcast_new_block(self, block):
        """
            将新生成的区块广播到网络中其他节点
        """
        for node in NODE_LIST:
            host = node['host']
            port = node['port']

            if host == self.host and port == self.port:
                print(self.name, "忽略自身节点")
            else:
                print(self.name, "广播新区块至 %s" % (node['name']))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))  # 连接到网络中的节点
                sock.send(pickle.dumps(block))  # 发送新区块
                sock.close()  # 发送完成后关闭连接

    def init_blockchain(self):
        """
            初始化当前节点的区块链
        """
        if NODE_LIST:  # 若当前网络中已存在其他节点，则从第一个节点从获取区块链信息
            host = NODE_LIST[0]['host']
            port = NODE_LIST[0]['port']
            name = NODE_LIST[0]["name"]
            print(self.name, "发送初始化请求 %s" % name)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))  # 连接到网络中的第一个节点
            sock.send(pickle.dumps('INIT'))  # 发送初始化请求
            data = []
            while True:  # 读取区块链信息，直至完全获取后退出
                buf = sock.recv(PER_BYTE)
                if not buf:
                    break
                data.append(buf)
                if len(buf) < PER_BYTE:
                    break
            sock.close()  # 获取完成后关闭连接

            # 将获取的区块链信息赋值到当前节点
            self.blockchain = pickle.loads(b''.join(data))
            print(self.name, "初始化完成.")
        else:
            # 如果是网络中的第一个节点，初始化一个创世区块
            block = Block(transactions=[], prev_hash="")
            w = ProofOfWork(block, self.wallet)
            genesis_block = w.mine()
            self.blockchain = BlockChain()
            self.blockchain.add_block(genesis_block)
            print("生成创世区块")

    def submit_transaction(self, transaction):
        for node in NODE_LIST:
            host = node['host']
            port = node['port']

            if host == self.host and port == self.port:
                print(self.name, "忽略自身节点")
            else:
                print(self.name, "广播新区块至 %s:%s" % (self.host, self.port))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((node["host"], node["port"]))
                sock.send(pickle.dumps(transaction))
                sock.close()

    def get_balance(self):
        balance = 0
        for block in self.blockchain.blocks:
            for t in block.transactions:
                if t.sender == self.wallet.address.decode():
                    balance -= t.amount
                elif t.recipient == self.wallet.address.decode():
                    balance += t.amount
        print("当前拥有%.1f个加密货币" % balance)

    def print_blockchain(self):
        print("区块链包含区块个数: %d\n" % len(self.blockchain.blocks))
        for block in self.blockchain.blocks:
            print("上个区块哈希：%s" % block.prev_hash)
            print("区块内容：%s" % block.transactions)
            print("区块哈希：%s" % block.hash)
            print("\n")


# 初始化节点1
node1 = Node("节点1", 8000)
node1.start()
node1.print_blockchain()

node2 = Node("节点2", 8001)
node2.start()
node2.print_blockchain()

node1.get_balance()
node2.get_balance()

new_transaction = Transaction(
    sender=node1.wallet.address,
    recipient=node2.wallet.address,
    amount=0.3
)
sig = node1.wallet.sign(str(new_transaction))
new_transaction.set_sign(sig, node1.wallet.pubkey)

node1.submit_transaction(new_transaction)
node1.print_blockchain()
node2.print_blockchain()
node1.get_balance()
node2.get_balance()

