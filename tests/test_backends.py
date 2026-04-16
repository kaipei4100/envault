"""Tests for envault.backends (LocalBackend)."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.backends import LocalBackend


@pytest.fixture()
def store(tmp_path: Path) -> LocalBackend:
    return LocalBackend(tmp_path / "store")


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    p = tmp_path / "vault.enc"
    p.write_bytes(b"encrypted-payload")
    return p


def test_store_dir_created_automatically(tmp_path: Path) -> None:
    backend = LocalBackend(tmp_path / "new" / "deep" / "dir")
    assert backend.store_dir.exists()


def test_upload_creates_file(store: LocalBackend, sample_file: Path) -> None:
    store.upload(sample_file, "project/v1.enc")
    assert (store.store_dir / "project" / "v1.enc").exists()


def test_upload_preserves_content(store: LocalBackend, sample_file: Path) -> None:
    store.upload(sample_file, "v1.enc")
    assert (store.store_dir / "v1.enc").read_bytes() == b"encrypted-payload"


def test_exists_returns_true_after_upload(store: LocalBackend, sample_file: Path) -> None:
    store.upload(sample_file, "v1.enc")
    assert store.exists("v1.enc") is True


def test_exists_returns_false_for_missing_key(store: LocalBackend) -> None:
    assert store.exists("nonexistent.enc") is False


def test_download_restores_file(store: LocalBackend, sample_file: Path, tmp_path: Path) -> None:
    store.upload(sample_file, "v1.enc")
    dest = tmp_path / "output" / "restored.enc"
    store.download("v1.enc", dest)
    assert dest.read_bytes() == b"encrypted-payload"


def test_download_creates_parent_dirs(store: LocalBackend, sample_file: Path, tmp_path: Path) -> None:
    store.upload(sample_file, "v1.enc")
    dest = tmp_path / "a" / "b" / "c" / "out.enc"
    store.download("v1.enc", dest)
    assert dest.exists()


def test_download_raises_for_missing_key(store: LocalBackend, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing.enc"):
        store.download("missing.enc", tmp_path / "out.enc")


def test_list_keys_empty_store(store: LocalBackend) -> None:
    assert store.list_keys() == []


def test_list_keys_returns_all_files(store: LocalBackend, sample_file: Path) -> None:
    store.upload(sample_file, "project/v1.enc")
    store.upload(sample_file, "project/v2.enc")
    keys = store.list_keys()
    assert len(keys) == 2
    assert all(".enc" in k for k in keys)


def test_list_keys_with_prefix(store: LocalBackend, sample_file: Path) -> None:
    store.upload(sample_file, "alpha/v1.enc")
    store.upload(sample_file, "beta/v1.enc")
    keys = store.list_keys(prefix="alpha")
    assert len(keys) == 1
    assert "alpha" in keys[0]


def test_list_keys_sorted(store: LocalBackend, sample_file: Path) -> None:
    for name in ["c.enc", "a.enc", "b.enc"]:
        store.upload(sample_file, name)
    assert store.list_keys() == ["a.enc", "b.enc", "c.enc"]
