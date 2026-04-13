"""Tests for envault.checksum."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.checksum import (
    ChecksumMismatch,
    _checksum_path,
    checksum_exists,
    compute,
    save_checksum,
    verify_checksum,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"encrypted-payload-data")
    return vf


def test_checksum_path_suffix(vault_file: Path) -> None:
    cp = _checksum_path(vault_file)
    assert cp.name.endswith(".checksum.json")


def test_compute_returns_hex_string() -> None:
    digest = compute(b"hello")
    assert isinstance(digest, str)
    assert len(digest) == 64  # sha256 hex length


def test_compute_is_deterministic() -> None:
    assert compute(b"data") == compute(b"data")


def test_compute_differs_for_different_data() -> None:
    assert compute(b"aaa") != compute(b"bbb")


def test_save_checksum_creates_file(vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    assert _checksum_path(vault_file).exists()


def test_save_checksum_returns_path(vault_file: Path) -> None:
    result = save_checksum(vault_file, vault_file.read_bytes())
    assert isinstance(result, Path)
    assert result == _checksum_path(vault_file)


def test_save_checksum_record_has_expected_keys(vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    record = json.loads(_checksum_path(vault_file).read_text())
    assert "algorithm" in record
    assert "digest" in record
    assert "vault" in record


def test_verify_checksum_passes_for_correct_data(vault_file: Path) -> None:
    data = vault_file.read_bytes()
    save_checksum(vault_file, data)
    digest = verify_checksum(vault_file, data)
    assert isinstance(digest, str) and len(digest) == 64


def test_verify_checksum_raises_on_mismatch(vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    with pytest.raises(ChecksumMismatch):
        verify_checksum(vault_file, b"tampered-data")


def test_verify_checksum_reads_file_when_data_omitted(vault_file: Path) -> None:
    data = vault_file.read_bytes()
    save_checksum(vault_file, data)
    digest = verify_checksum(vault_file)  # no explicit data
    assert digest == compute(data)


def test_verify_checksum_raises_when_no_checksum_file(vault_file: Path) -> None:
    with pytest.raises(FileNotFoundError):
        verify_checksum(vault_file)


def test_checksum_exists_true_after_save(vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    assert checksum_exists(vault_file) is True


def test_checksum_exists_false_before_save(vault_file: Path) -> None:
    assert checksum_exists(vault_file) is False
