"""Tests for envault.annotate."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.annotate import (
    _annotation_path,
    set_annotation,
    get_annotation,
    delete_annotation,
    list_annotations,
    AnnotationNotFound,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "my.vault"
    p.write_bytes(b"dummy")
    return p


def test_annotation_path_has_correct_suffix(vault_file):
    path = _annotation_path(vault_file)
    assert path.name.endswith(".annotations.json")


def test_annotation_path_sibling_of_vault(vault_file):
    path = _annotation_path(vault_file)
    assert path.parent == vault_file.parent


def test_annotation_path_contains_stem(vault_file):
    path = _annotation_path(vault_file)
    assert vault_file.stem in path.name


def test_get_annotation_raises_when_missing(vault_file):
    with pytest.raises(AnnotationNotFound):
        get_annotation(vault_file, 1)


def test_set_annotation_creates_file(vault_file):
    set_annotation(vault_file, 1, "initial release")
    assert _annotation_path(vault_file).exists()


def test_set_annotation_returns_dict_with_expected_keys(vault_file):
    entry = set_annotation(vault_file, 1, "hello")
    assert "version" in entry
    assert "note" in entry
    assert "timestamp" in entry


def test_set_annotation_stores_note(vault_file):
    set_annotation(vault_file, 2, "hotfix")
    entry = get_annotation(vault_file, 2)
    assert entry["note"] == "hotfix"


def test_set_annotation_stores_version(vault_file):
    set_annotation(vault_file, 3, "bump")
    entry = get_annotation(vault_file, 3)
    assert entry["version"] == 3


def test_set_annotation_with_author(vault_file):
    set_annotation(vault_file, 1, "authored", author="alice")
    entry = get_annotation(vault_file, 1)
    assert entry["author"] == "alice"


def test_set_annotation_without_author_has_no_author_key(vault_file):
    set_annotation(vault_file, 1, "no author")
    entry = get_annotation(vault_file, 1)
    assert "author" not in entry


def test_set_annotation_overwrites_existing(vault_file):
    set_annotation(vault_file, 1, "first")
    set_annotation(vault_file, 1, "second")
    entry = get_annotation(vault_file, 1)
    assert entry["note"] == "second"


def test_delete_annotation_returns_true_when_exists(vault_file):
    set_annotation(vault_file, 1, "to delete")
    assert delete_annotation(vault_file, 1) is True


def test_delete_annotation_returns_false_when_missing(vault_file):
    assert delete_annotation(vault_file, 99) is False


def test_delete_annotation_removes_entry(vault_file):
    set_annotation(vault_file, 1, "bye")
    delete_annotation(vault_file, 1)
    with pytest.raises(AnnotationNotFound):
        get_annotation(vault_file, 1)


def test_list_annotations_returns_sorted(vault_file):
    set_annotation(vault_file, 3, "c")
    set_annotation(vault_file, 1, "a")
    set_annotation(vault_file, 2, "b")
    entries = list_annotations(vault_file)
    assert [e["version"] for e in entries] == [1, 2, 3]


def test_list_annotations_empty_when_no_file(vault_file):
    assert list_annotations(vault_file) == []
