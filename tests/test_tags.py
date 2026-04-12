"""Tests for envault.tags."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.tags import (
    set_tag,
    delete_tag,
    resolve_tag,
    list_tags,
    find_tags_for_version,
    _tags_path,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_tag_creates_tags_file(vault_dir):
    set_tag(vault_dir, "stable", 3)
    assert _tags_path(vault_dir).exists()


def test_resolve_tag_returns_correct_version(vault_dir):
    set_tag(vault_dir, "stable", 3)
    assert resolve_tag(vault_dir, "stable") == 3


def test_set_tag_overwrites_existing(vault_dir):
    set_tag(vault_dir, "stable", 3)
    set_tag(vault_dir, "stable", 7)
    assert resolve_tag(vault_dir, "stable") == 7


def test_resolve_missing_tag_raises(vault_dir):
    with pytest.raises(KeyError, match="nope"):
        resolve_tag(vault_dir, "nope")


def test_delete_tag_removes_it(vault_dir):
    set_tag(vault_dir, "beta", 2)
    delete_tag(vault_dir, "beta")
    with pytest.raises(KeyError):
        resolve_tag(vault_dir, "beta")


def test_delete_missing_tag_raises(vault_dir):
    with pytest.raises(KeyError, match="ghost"):
        delete_tag(vault_dir, "ghost")


def test_list_tags_sorted(vault_dir):
    set_tag(vault_dir, "zeta", 5)
    set_tag(vault_dir, "alpha", 1)
    set_tag(vault_dir, "beta", 2)
    names = [entry["tag"] for entry in list_tags(vault_dir)]
    assert names == ["alpha", "beta", "zeta"]


def test_list_tags_empty_when_no_file(vault_dir):
    assert list_tags(vault_dir) == []


def test_find_tags_for_version(vault_dir):
    set_tag(vault_dir, "stable", 4)
    set_tag(vault_dir, "release", 4)
    set_tag(vault_dir, "dev", 5)
    result = find_tags_for_version(vault_dir, 4)
    assert result == ["release", "stable"]


def test_find_tags_for_version_none_match(vault_dir):
    set_tag(vault_dir, "stable", 3)
    assert find_tags_for_version(vault_dir, 99) == []


def test_invalid_tag_name_raises(vault_dir):
    with pytest.raises(ValueError, match="Invalid tag name"):
        set_tag(vault_dir, "my-tag", 1)


def test_multiple_tags_independent(vault_dir):
    set_tag(vault_dir, "v1", 1)
    set_tag(vault_dir, "v2", 2)
    assert resolve_tag(vault_dir, "v1") == 1
    assert resolve_tag(vault_dir, "v2") == 2
