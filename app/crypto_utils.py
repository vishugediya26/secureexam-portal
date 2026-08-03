import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def get_key():
    key_b64 = os.getenv('ENCRYPTION_KEY')
    return base64.b64decode(key_b64)

def encrypt_text(plaintext: str) -> bytes:
    key = get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ciphertext

def decrypt_text(blob: bytes) -> str:
    key = get_key()
    aesgcm = AESGCM(key)
    nonce = blob[:12]
    ciphertext = blob[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()