"""Tests for envault.alias."""
import pytest
from pathlib import Path
from envault.alias import (
    _alias_path,
    set_alias,
    get_alias,
    delete_alias,
    list_aliases,
    resolve,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"dummy")
    return vf


def test_alias_path_has_correct_suffix(vault_file):
    ap = _alias_path(vault_file)
    assert ap.name == "test.aliases.json"


def test_alias_path_sibling_of_vault(vault_file):
    ap = _alias_path(vault_file)
    assert ap.parent == vault_file.parent


def test_get_alias_returns_none_when_missing(vault_file):
    assert get_alias(vault_file, "db") is None


def test_set_alias_persists(vault_file):
    set_alias(vault_file, "db", "DATABASE_URL")
    assert get_alias(vault_file, "db") == "DATABASE_URL"


def test_set_alias_returns_dict(vault_file):
    result = set_alias(vault_file, "db", "DATABASE_URL")
    assert result == {"alias": "db", "key": "DATABASE_URL"}


def test_set_alias_overwrites_existing(vault_file):
    set_alias(vault_file, "db", "DATABASE_URL")
    set_alias(vault_file, "db", "POSTGRES_URL")
    assert get_alias(vault_file, "db") == "POSTGRES_URL"


def test_set_alias_empty_alias_raises(vault_file):
    with pytest.raises(ValueError):
        set_alias(vault_file, "", "DATABASE_URL")


def test_set_alias_empty_key_raises(vault_file):
    with pytest.raises(ValueError):
        set_alias(vault_file, "db", "")


def test_delete_alias_returns_true_when_exists(vault_file):
    set_alias(vault_file, "db", "DATABASE_URL")
    assert delete_alias(vault_file, "db") is True


def test_delete_alias_returns_false_when_missing(vault_file):
    assert delete_alias(vault_file, "nope") is False


def test_delete_alias_removes_entry(vault_file):
    set_alias(vault_file, "db", "DATABASE_URL")
    delete_alias(vault_file, "db")
    assert get_alias(vault_file, "db") is None


def test_list_aliases_returns_sorted(vault_file):
    set_alias(vault_file, "z_key", "Z")
    set_alias(vault_file, "a_key", "A")
    keys = list(list_aliases(vault_file).keys())
    assert keys == sorted(keys)


def test_resolve_known_alias(vault_file):
    set_alias(vault_file, "db", "DATABASE_URL")
    assert resolve(vault_file, "db") == "DATABASE_URL"


def test_resolve_unknown_falls_back_to_input(vault_file):
    assert resolve(vault_file, "DATABASE_URL") == "DATABASE_URL"
