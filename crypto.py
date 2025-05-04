import os
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Cipher import AES

class CryptoEngine:
    """
    CryptoEngine provides symmetric encryption and decryption using AES-GCM
    with keys derived from a passphrase and salt via PBKDF2.
    """

    def __init__(self, passphrase: str, salt: bytes):
        """
        Initialize the engine with a user-supplied passphrase and salt.
        Derives a 128-bit AES key via PBKDF2.
        """
        self.passphrase = passphrase
        self.salt = salt
        self._derive_key()  # derive self.key

    def _derive_key(self):
        """
        Perform PBKDF2 key derivation:
        - passphrase: user input
        - salt: 16-byte random salt
        - dkLen: 16 bytes → 128-bit AES key
        - count: 200,000 iterations for work factor
        - HMAC-SHA256 as the pseudorandom function
        """
        self.key = PBKDF2(
            self.passphrase,
            self.salt,
            dkLen=16,
            count=200_000,
            hmac_hash_module=SHA256
        )

    @staticmethod
    def generate_salt() -> bytes:
        """
        Generate a fresh 16-byte salt using a cryptographically secure RNG.
        """
        return os.urandom(16)

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext with AES-GCM:
        - Generate a 12-byte nonce
        - Encrypt and compute a 16-byte authentication tag
        - Return concatenated message: nonce || tag || ciphertext
        """
        nonce = os.urandom(12)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ct, tag = cipher.encrypt_and_digest(plaintext)
        return nonce + tag + ct

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data encrypted by this engine:
        - Extract nonce (first 12 bytes)
        - Extract tag (next 16 bytes)
        - Remaining bytes are the ciphertext
        - Verify tag and return plaintext
        """
        nonce = data[:12]
        tag   = data[12:28]
        ct    = data[28:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ct, tag)

    def rekey(self) -> bytes:
        """
        Rotate the symmetric key:
        - Generate a new salt
        - Re-derive the key with the same passphrase
        - Return the new salt so it can be shared with a peer
        """
        new_salt = self.generate_salt()
        self.salt = new_salt
        self._derive_key()
        return new_salt
