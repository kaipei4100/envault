"""Tests for envault.archive."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from envault.vault import write_vault
from envault.snapshot import save_snapshot
from envault.archive import (
    _archive_path,
    create_archive,
    list_archived,
    restore_from_archive,
)

PASSWORD = "archivepass"
ENV = {"KEY": "value", "FOO": "bar"}


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    write_vault(vf, ENV, PASSWORD)
    # create several snapshots
    for _ in range(5):
        save_snapshot(vf, ENV, PASSWORD)
    return vf


def test_archive_path_has_correct_suffix(vault_file: Path) -> None:
    assert _archive_path(vault_file).suffix == ".zip"


def test_archive_path_sibling_of_vault(vault_file: Path) -> None:
    assert _archive_path(vault_file).parent == vault_file.parent


def test_create_archive_returns_result(vault_file: Path) -> None:
    result = create_archive(vault_file, PASSWORD, keep_latest=3)
    assert result is not None


def test_create_archive_archives_old_versions(vault_file: Path) -> None:
    result = create_archive(vault_file, PASSWORD, keep_latest=3)
    assert len(result.versions) == 2


def test_create_archive_creates_zip_file(vault_file: Path) -> None:
    create_archive(vault_file, PASSWORD, keep_latest=3)
    assert _archive_path(vault_file).exists()


def test_create_archive_removes_old_snapshot_files(vault_file: Path) -> None:
    from envault.snapshot import _snapshot_dir
    create_archive(vault_file, PASSWORD, keep_latest=3)
    snap_dir = _snapshot_dir(vault_file)
    remaining = list(snap_dir.glob("*.enc"))
    assert len(remaining) == 3


def test_create_archive_nothing_to_do_when_few_snapshots(vault_file: Path) -> None:
    result = create_archive(vault_file, PASSWORD, keep_latest=10)
    assert result.versions == []


def test_list_archived_returns_empty_when_no_archive(vault_file: Path) -> None:
    assert list_archived(vault_file) == []


def test_list_archived_returns_versions(vault_file: Path) -> None:
    create_archive(vault_file, PASSWORD, keep_latest=3)
    versions = list_archived(vault_file)
    assert len(versions) == 2
    assert all(isinstance(v, int) for v in versions)


def test_list_archived_sorted(vault_file: Path) -> None:
    create_archive(vault_file, PASSWORD, keep_latest=3)
    versions = list_archived(vault_file)
    assert versions == sorted(versions)


def test_restore_from_archive_recreates_file(vault_file: Path) -> None:
    from envault.snapshot import _snapshot_dir
    result = create_archive(vault_file, PASSWORD, keep_latest=3)
    version = result.versions[0]
    restored = restore_from_archive(vault_file, version)
    assert restored.exists()


def test_restore_missing_version_raises(vault_file: Path) -> None:
    create_archive(vault_file, PASSWORD, keep_latest=3)
    with pytest.raises(KeyError):
        restore_from_archive(vault_file, 999)


def test_restore_no_archive_raises(vault_file: Path) -> None:
    with pytest.raises(FileNotFoundError):
        restore_from_archive(vault_file, 1)
