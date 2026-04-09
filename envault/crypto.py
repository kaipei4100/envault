"""Encryption and decryption utilities for .env files using AES-GCM via Fernet."""

import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
KDF_ITERATIONS = 390_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from a password and salt using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt(plaintext: str, password: str) -> bytes:
    """
    Encrypt plaintext using a password.

    Returns salt + encrypted bytes (salt is prepended for storage).
    """
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext.encode())
    return salt + encrypted


def decrypt(ciphertext: bytes, password: str) -> str:
    """
    Decrypt ciphertext using a password.

    Expects salt to be prepended to the encrypted bytes.

    Raises:
        ValueError: If decryption fails due to wrong password or corrupted data.
    """
    if len(ciphertext) <= SALT_SIZE:
        raise ValueError("Ciphertext is too short to contain a valid salt.")

    salt = ciphertext[:SALT_SIZE]
    encrypted = ciphertext[SALT_SIZE:]
    key = derive_key(password, salt)
    fernet = Fernet(key)

    try:
        return fernet.decrypt(encrypted).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid password or corrupted data.") from exc


def fingerprint(ciphertext: bytes) -> str:
    """Return a short SHA-256 hex fingerprint of the ciphertext for version identification."""
    digest = hashlib.sha256(ciphertext).hexdigest()
    return digest[:12]
