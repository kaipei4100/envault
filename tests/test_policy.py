"""Tests for envault.policy."""
import pytest
from pathlib import Path
from envault.policy import (
    Policy,
    load_policy,
    save_policy,
    check_operation,
    PolicyViolation,
    POLICY_FILE,
)


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / "vault"


def test_load_policy_missing_file_returns_defaults(vault_dir):
    policy = load_policy(vault_dir)
    assert isinstance(policy, Policy)
    assert policy.require_note is False
    assert policy.min_password_length == 8
    assert policy.read_only is False
    assert policy.max_versions is None


def test_save_and_load_policy_roundtrip(vault_dir):
    policy = Policy(
        allowed_operations=["lock", "unlock"],
        require_note=True,
        min_password_length=12,
        max_versions=5,
        read_only=False,
    )
    save_policy(vault_dir, policy)
    loaded = load_policy(vault_dir)
    assert loaded.allowed_operations == ["lock", "unlock"]
    assert loaded.require_note is True
    assert loaded.min_password_length == 12
    assert loaded.max_versions == 5


def test_save_policy_creates_file(vault_dir):
    save_policy(vault_dir, Policy())
    assert (vault_dir / POLICY_FILE).exists()


def test_check_operation_allowed_returns_none(vault_dir):
    policy = load_policy(vault_dir)
    result = check_operation(policy, "lock", note=None, password="strongpass")
    assert result is None


def test_check_operation_disallowed_returns_violation():
    policy = Policy(allowed_operations=["lock"])
    result = check_operation(policy, "push")
    assert isinstance(result, PolicyViolation)
    assert "push" in str(result)


def test_check_operation_read_only_blocks_write():
    policy = Policy(read_only=True)
    result = check_operation(policy, "lock")
    assert isinstance(result, PolicyViolation)
    assert "read-only" in str(result)


def test_check_operation_read_only_allows_unlock():
    policy = Policy(read_only=True)
    result = check_operation(policy, "unlock")
    assert result is None


def test_check_operation_require_note_without_note_fails():
    policy = Policy(require_note=True)
    result = check_operation(policy, "lock", note=None)
    assert isinstance(result, PolicyViolation)
    assert "note" in str(result).lower()


def test_check_operation_require_note_with_note_passes():
    policy = Policy(require_note=True)
    result = check_operation(policy, "lock", note="bumping secrets")
    assert result is None


def test_check_operation_short_password_fails():
    policy = Policy(min_password_length=16)
    result = check_operation(policy, "lock", password="short")
    assert isinstance(result, PolicyViolation)
    assert "16" in str(result)


def test_check_operation_sufficient_password_passes():
    policy = Policy(min_password_length=8)
    result = check_operation(policy, "lock", password="longenoughpass")
    assert result is None
