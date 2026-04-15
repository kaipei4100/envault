"""Tests for envault.retention."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.retention import (
    _retention_path,
    set_retention,
    get_retention,
    delete_retention,
    apply_retention,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


def test_retention_path_has_correct_suffix(vault_file: Path) -> None:
    assert _retention_path(vault_file).name == "secrets.retention.json"


def test_retention_path_sibling_of_vault(vault_file: Path) -> None:
    assert _retention_path(vault_file).parent == vault_file.parent


def test_get_retention_returns_none_when_missing(vault_file: Path) -> None:
    assert get_retention(vault_file) is None


def test_set_retention_creates_file(vault_file: Path) -> None:
    set_retention(vault_file, keep=5)
    assert _retention_path(vault_file).exists()


def test_set_retention_returns_dict_with_keep(vault_file: Path) -> None:
    result = set_retention(vault_file, keep=3)
    assert result["keep"] == 3


def test_get_retention_returns_correct_value(vault_file: Path) -> None:
    set_retention(vault_file, keep=7)
    assert get_retention(vault_file) == 7


def test_set_retention_overwrites_existing(vault_file: Path) -> None:
    set_retention(vault_file, keep=10)
    set_retention(vault_file, keep=2)
    assert get_retention(vault_file) == 2


def test_set_retention_raises_for_zero(vault_file: Path) -> None:
    with pytest.raises(ValueError):
        set_retention(vault_file, keep=0)


def test_set_retention_raises_for_negative(vault_file: Path) -> None:
    with pytest.raises(ValueError):
        set_retention(vault_file, keep=-1)


def test_delete_retention_returns_true_when_existed(vault_file: Path) -> None:
    set_retention(vault_file, keep=3)
    assert delete_retention(vault_file) is True


def test_delete_retention_removes_file(vault_file: Path) -> None:
    set_retention(vault_file, keep=3)
    delete_retention(vault_file)
    assert not _retention_path(vault_file).exists()


def test_delete_retention_returns_false_when_missing(vault_file: Path) -> None:
    assert delete_retention(vault_file) is False


def test_apply_retention_no_policy_returns_empty(vault_file: Path) -> None:
    assert apply_retention(vault_file, [1, 2, 3, 4, 5]) == []


def test_apply_retention_prunes_oldest_versions(vault_file: Path) -> None:
    set_retention(vault_file, keep=3)
    to_prune = apply_retention(vault_file, [1, 2, 3, 4, 5])
    assert to_prune == [1, 2]


def test_apply_retention_keeps_all_when_under_limit(vault_file: Path) -> None:
    set_retention(vault_file, keep=10)
    assert apply_retention(vault_file, [1, 2, 3]) == []


def test_apply_retention_single_version_kept(vault_file: Path) -> None:
    set_retention(vault_file, keep=1)
    assert apply_retention(vault_file, [1, 2, 3]) == [1, 2]
