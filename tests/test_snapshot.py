"""Tests for envault.snapshot."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import write_vault
from envault.snapshot import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    restore_snapshot,
    _snapshot_path,
)

PASSWORD = "hunter2"
SAMPLE_ENV = {"APP_ENV": "production", "SECRET": "abc123"}


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vpath = tmp_path / "secrets.vault"
    write_vault(vpath, SAMPLE_ENV, PASSWORD)
    return vpath


def test_save_snapshot_creates_file(vault_file: Path) -> None:
    result = save_snapshot(vault_file, PASSWORD)
    snap = Path(result["path"])
    assert snap.exists()


def test_save_snapshot_returns_correct_version(vault_file: Path) -> None:
    result = save_snapshot(vault_file, PASSWORD)
    assert result["version"] == 1


def test_load_snapshot_roundtrip(vault_file: Path) -> None:
    save_snapshot(vault_file, PASSWORD)
    env = load_snapshot(vault_file, 1, PASSWORD)
    assert env == SAMPLE_ENV


def test_load_snapshot_wrong_password_raises(vault_file: Path) -> None:
    save_snapshot(vault_file, PASSWORD)
    with pytest.raises(Exception):
        load_snapshot(vault_file, 1, "wrongpassword")


def test_load_snapshot_missing_version_raises(vault_file: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshot(vault_file, 99, PASSWORD)


def test_list_snapshots_empty_before_save(vault_file: Path) -> None:
    assert list_snapshots(vault_file) == []


def test_list_snapshots_after_save(vault_file: Path) -> None:
    save_snapshot(vault_file, PASSWORD)
    versions = list_snapshots(vault_file)
    assert versions == [1]


def test_list_snapshots_sorted(vault_file: Path, tmp_path: Path) -> None:
    """Manually create snap files for multiple versions and check ordering."""
    from envault.snapshot import _snapshot_dir
    snap_dir = _snapshot_dir(vault_file)
    snap_dir.mkdir(parents=True, exist_ok=True)
    for v in [3, 1, 2]:
        _snapshot_path(vault_file, v).write_bytes(b"dummy")
    assert list_snapshots(vault_file) == [1, 2, 3]


def test_restore_snapshot_writes_env_file(vault_file: Path) -> None:
    save_snapshot(vault_file, PASSWORD)
    content = restore_snapshot(vault_file, 1, PASSWORD)
    env_file = vault_file.parent / ".env"
    assert env_file.exists()
    assert env_file.read_text() == content


def test_restore_snapshot_content_contains_keys(vault_file: Path) -> None:
    save_snapshot(vault_file, PASSWORD)
    content = restore_snapshot(vault_file, 1, PASSWORD)
    assert "APP_ENV" in content
    assert "SECRET" in content
