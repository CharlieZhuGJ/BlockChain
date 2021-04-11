import hashlib
import base64
import binascii
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadDigestError


class Wallet(object):
    def __init__(self):
        self._private_key = SigningKey.generate(curve=SECP256k1)
        self._public_key = self._private_key.get_verifying_key()

    @property
    def address(self):
        h = hashlib.sha256()
        return base64.b64encode(h.digest())

    @property
    def pubkey(self):
        return self._public_key.to_pem()

    def sign(self, message):
        h = hashlib.sha256(message.encode('utf8'))
        return binascii.hexlify(self._private_key.sign(h.digest()))


def verify_sign(pubkey, message, signature):
    verifier = VerifyingKey.from_pem(pubkey)
    h = hashlib.sha256(message.encode('utf8'))
    return verifier.verify(binascii.unhexlify(signature), h.digest())


w = Wallet()
print(w.address)
print(w.pubkey)
data = "交易数据"
sig = w.sign(data)
print(sig)


verify_sign(w.pubkey, data, sig)


