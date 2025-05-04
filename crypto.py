import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


class CryptoEngine:
    def __init__(self, passphrase: str, salt: bytes):
        self.passphrase = passphrase
        self.salt = salt
        self._derive_key()

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=16,  # 128-bit AES key
            salt=self.salt,
            iterations=200_000,
            backend=default_backend()
        )
        self.key = kdf.derive(self.passphrase.encode())

    @staticmethod
    def generate_salt() -> bytes:
        return os.urandom(16)

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = os.urandom(12)  # AESGCM requires a 96-bit nonce
        aesgcm = AESGCM(self.key)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct  # ciphertext already includes the tag

    def decrypt(self, data: bytes) -> bytes:
        nonce = data[:12]
        ct = data[12:]
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ct, None)

    def rekey(self) -> bytes:
        new_salt = self.generate_salt()
        self.salt = new_salt
        self._derive_key()
        return new_salt
