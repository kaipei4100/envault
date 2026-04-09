"""Tests for envault.vault — write/read/version cycle."""

import json
import time

import pytest

from envault.vault import read_vault, vault_metadata, write_vault

PASSWORD = "super-secret-42"
SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


@pytest.fixture()
def vault_file(tmp_path):
    return tmp_path / "test.vault"


def test_write_creates_vault_file(vault_file):
    write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    assert vault_file.exists()
    assert vault_file.stat().st_size > 0


def test_write_creates_meta_file(vault_file):
    write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    meta_path = vault_file.parent / "test.vault.meta"
    assert meta_path.exists()


def test_meta_contains_expected_keys(vault_file):
    meta = write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    for key in ("version", "fingerprint", "timestamp", "comment"):
        assert key in meta


def test_meta_version_starts_at_one(vault_file):
    meta = write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    assert meta["version"] == 1


def test_meta_version_increments(vault_file):
    write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    meta2 = write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    assert meta2["version"] == 2


def test_meta_timestamp_is_recent(vault_file):
    before = int(time.time())
    meta = write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    after = int(time.time())
    assert before <= meta["timestamp"] <= after


def test_read_vault_roundtrip(vault_file):
    write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    plaintext = read_vault(vault_file, PASSWORD)
    assert plaintext == SAMPLE_ENV


def test_read_vault_wrong_password_raises(vault_file):
    write_vault(SAMPLE_ENV, PASSWORD, vault_file)
    with pytest.raises(Exception):
        read_vault(vault_file, "wrong-password")


def test_vault_metadata_returns_none_when_missing(tmp_path):
    vault_path = tmp_path / "empty.vault"
    vault_path.write_bytes(b"placeholder")
    assert vault_metadata(vault_path) is None


def test_meta_comment_stored(vault_file):
    meta = write_vault(SAMPLE_ENV, PASSWORD, vault_file, comment="initial commit")
    assert meta["comment"] == "initial commit"
