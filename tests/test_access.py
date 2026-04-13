"""Tests for envault.access."""
import pytest
from pathlib import Path
from envault.access import (
    set_permission,
    get_permission,
    revoke_permission,
    list_permissions,
    check_permission,
    READ, WRITE, ADMIN,
)


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_set_and_get_permission(vault_dir):
    set_permission(vault_dir, "alice", READ)
    assert get_permission(vault_dir, "alice") == READ


def test_get_missing_identity_returns_none(vault_dir):
    assert get_permission(vault_dir, "nobody") is None


def test_set_invalid_level_raises(vault_dir):
    with pytest.raises(ValueError, match="Unknown permission level"):
        set_permission(vault_dir, "alice", "superuser")


def test_set_overwrites_existing_permission(vault_dir):
    set_permission(vault_dir, "alice", READ)
    set_permission(vault_dir, "alice", ADMIN)
    assert get_permission(vault_dir, "alice") == ADMIN


def test_revoke_removes_identity(vault_dir):
    set_permission(vault_dir, "bob", WRITE)
    revoke_permission(vault_dir, "bob")
    assert get_permission(vault_dir, "bob") is None


def test_revoke_missing_identity_raises(vault_dir):
    with pytest.raises(KeyError, match="bob"):
        revoke_permission(vault_dir, "bob")


def test_list_permissions_sorted(vault_dir):
    set_permission(vault_dir, "zara", READ)
    set_permission(vault_dir, "alice", ADMIN)
    set_permission(vault_dir, "mike", WRITE)
    result = list_permissions(vault_dir)
    assert [r["identity"] for r in result] == ["alice", "mike", "zara"]


def test_list_permissions_empty(vault_dir):
    assert list_permissions(vault_dir) == []


def test_check_permission_passes_exact_level(vault_dir):
    set_permission(vault_dir, "alice", WRITE)
    check_permission(vault_dir, "alice", WRITE)  # should not raise


def test_check_permission_passes_higher_level(vault_dir):
    set_permission(vault_dir, "alice", ADMIN)
    check_permission(vault_dir, "alice", READ)  # admin >= read


def test_check_permission_fails_insufficient_level(vault_dir):
    set_permission(vault_dir, "alice", READ)
    with pytest.raises(PermissionError, match="'write' is required"):
        check_permission(vault_dir, "alice", WRITE)


def test_check_permission_fails_no_access(vault_dir):
    with pytest.raises(PermissionError, match="no access permissions"):
        check_permission(vault_dir, "ghost", READ)


def test_access_file_created_on_first_set(vault_dir):
    from envault.access import _access_path
    assert not _access_path(vault_dir).exists()
    set_permission(vault_dir, "alice", READ)
    assert _access_path(vault_dir).exists()
