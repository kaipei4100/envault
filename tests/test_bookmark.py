"""Tests for envault.bookmark."""
from __future__ import annotations

import json
import pytest

from envault.bookmark import (
    BookmarkNotFound,
    _bookmark_path,
    delete_bookmark,
    get_bookmark,
    list_bookmarks,
    set_bookmark,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


# --- path helpers ---

def test_bookmark_path_has_correct_suffix(vault_file):
    assert _bookmark_path(vault_file).suffix == ".json"


def test_bookmark_path_sibling_of_vault(vault_file):
    assert _bookmark_path(vault_file).parent == vault_file.parent


def test_bookmark_path_contains_bookmarks_in_name(vault_file):
    assert "bookmarks" in _bookmark_path(vault_file).name


# --- set_bookmark ---

def test_set_bookmark_creates_file(vault_file):
    set_bookmark(vault_file, "stable", 3)
    assert _bookmark_path(vault_file).exists()


def test_set_bookmark_returns_dict(vault_file):
    result = set_bookmark(vault_file, "stable", 3)
    assert result == {"label": "stable", "version": 3}


def test_set_bookmark_persists(vault_file):
    set_bookmark(vault_file, "release", 7)
    raw = json.loads(_bookmark_path(vault_file).read_text())
    assert raw["release"] == 7


def test_set_bookmark_overwrites_existing(vault_file):
    set_bookmark(vault_file, "stable", 2)
    set_bookmark(vault_file, "stable", 5)
    assert get_bookmark(vault_file, "stable") == 5


def test_set_bookmark_empty_label_raises(vault_file):
    with pytest.raises(ValueError, match="label"):
        set_bookmark(vault_file, "", 1)


def test_set_bookmark_zero_version_raises(vault_file):
    with pytest.raises(ValueError, match="positive"):
        set_bookmark(vault_file, "bad", 0)


# --- get_bookmark ---

def test_get_bookmark_returns_correct_version(vault_file):
    set_bookmark(vault_file, "v1", 4)
    assert get_bookmark(vault_file, "v1") == 4


def test_get_missing_bookmark_raises(vault_file):
    with pytest.raises(BookmarkNotFound):
        get_bookmark(vault_file, "nonexistent")


# --- delete_bookmark ---

def test_delete_bookmark_removes_label(vault_file):
    set_bookmark(vault_file, "old", 1)
    delete_bookmark(vault_file, "old")
    with pytest.raises(BookmarkNotFound):
        get_bookmark(vault_file, "old")


def test_delete_missing_bookmark_raises(vault_file):
    with pytest.raises(BookmarkNotFound):
        delete_bookmark(vault_file, "ghost")


# --- list_bookmarks ---

def test_list_bookmarks_empty_when_no_file(vault_file):
    assert list_bookmarks(vault_file) == []


def test_list_bookmarks_returns_all(vault_file):
    set_bookmark(vault_file, "beta", 2)
    set_bookmark(vault_file, "alpha", 1)
    labels = [b["label"] for b in list_bookmarks(vault_file)]
    assert labels == ["alpha", "beta"]


def test_list_bookmarks_sorted_alphabetically(vault_file):
    for lbl, ver in [("z", 3), ("a", 1), ("m", 2)]:
        set_bookmark(vault_file, lbl, ver)
    result = list_bookmarks(vault_file)
    assert [r["label"] for r in result] == ["a", "m", "z"]
