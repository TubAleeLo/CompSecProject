import os
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Cipher import AES

class CryptoEngine:
    def __init__(self, passphrase: str, salt: bytes):
        # Derive a 128-bit key via PBKDF2
        self.passphrase = passphrase
        self.salt = salt
        self._derive_key()

    def _derive_key(self):
        self.key = PBKDF2(
            self.passphrase,
            self.salt,
            dkLen=16,
            count=200_000,
            hmac_hash_module=SHA256
        )

    @staticmethod
    def generate_salt() -> bytes:
        return os.urandom(16)

    def encrypt(self, plaintext: bytes) -> bytes:
        # AES-GCM: 12-byte nonce, 16-byte tag
        nonce = os.urandom(12)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ct, tag = cipher.encrypt_and_digest(plaintext)
        # [nonce||tag||ciphertext]
        return nonce + tag + ct

    def decrypt(self, data: bytes) -> bytes:
        nonce, tag, ct = data[:12], data[12:28], data[28:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ct, tag)

    def rekey(self) -> bytes:
        # Generate a new salt, derive fresh key, return salt to send
        new_salt = self.generate_salt()
        self.salt = new_salt
        self._derive_key()
        return new_salt
