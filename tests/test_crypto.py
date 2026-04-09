"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt, fingerprint, SALT_SIZE


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "DB_HOST=localhost\nDB_PASS=hunter2\nAPI_KEY=abc123"


def test_encrypt_returns_bytes():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(result, bytes)


def test_encrypted_output_longer_than_salt():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert len(result) > SALT_SIZE


def test_decrypt_roundtrip():
    ciphertext = encrypt(PLAINTEXT, PASSWORD)
    recovered = decrypt(ciphertext, PASSWORD)
    assert recovered == PLAINTEXT


def test_decrypt_wrong_password_raises():
    ciphertext = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(ciphertext, "wrong-password")


def test_decrypt_corrupted_data_raises():
    ciphertext = bytearray(encrypt(PLAINTEXT, PASSWORD))
    ciphertext[SALT_SIZE + 5] ^= 0xFF  # flip a byte in the encrypted portion
    with pytest.raises(ValueError):
        decrypt(bytes(ciphertext), PASSWORD)


def test_decrypt_too_short_raises():
    with pytest.raises(ValueError, match="too short"):
        decrypt(b"tooshort", PASSWORD)


def test_encrypt_produces_different_ciphertext_each_time():
    ct1 = encrypt(PLAINTEXT, PASSWORD)
    ct2 = encrypt(PLAINTEXT, PASSWORD)
    assert ct1 != ct2, "Each encryption should use a fresh random salt"


def test_fingerprint_is_12_chars():
    ciphertext = encrypt(PLAINTEXT, PASSWORD)
    fp = fingerprint(ciphertext)
    assert isinstance(fp, str)
    assert len(fp) == 12


def test_fingerprint_is_deterministic():
    ciphertext = encrypt(PLAINTEXT, PASSWORD)
    assert fingerprint(ciphertext) == fingerprint(ciphertext)


def test_fingerprint_differs_for_different_ciphertexts():
    ct1 = encrypt(PLAINTEXT, PASSWORD)
    ct2 = encrypt(PLAINTEXT, PASSWORD)
    assert fingerprint(ct1) != fingerprint(ct2)
