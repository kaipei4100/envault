"""Tests for envault.lock_status."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.lock_status import (
    _status_path,
    set_locked,
    set_unlocked,
    get_status,
    is_locked,
    assert_unlocked,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


def test_status_path_has_correct_suffix(vault_file):
    assert _status_path(vault_file).suffix == ".lockstatus"


def test_status_path_sibling_of_vault(vault_file):
    assert _status_path(vault_file).parent == vault_file.parent


def test_get_status_returns_unlocked_when_missing(vault_file):
    status = get_status(vault_file)
    assert status["locked"] is False
    assert status["identity"] is None


def test_set_locked_creates_status_file(vault_file):
    set_locked(vault_file, "alice")
    assert _status_path(vault_file).exists()


def test_set_locked_returns_dict_with_expected_keys(vault_file):
    result = set_locked(vault_file, "alice", note="maintenance")
    assert "locked" in result
    assert "identity" in result
    assert "locked_at" in result
    assert "note" in result


def test_set_locked_marks_as_locked(vault_file):
    set_locked(vault_file, "alice")
    assert is_locked(vault_file) is True


def test_set_locked_records_identity(vault_file):
    set_locked(vault_file, "bob")
    assert get_status(vault_file)["identity"] == "bob"


def test_set_locked_records_note(vault_file):
    set_locked(vault_file, "alice", note="rotating keys")
    assert get_status(vault_file)["note"] == "rotating keys"


def test_set_unlocked_clears_lock(vault_file):
    set_locked(vault_file, "alice")
    set_unlocked(vault_file)
    assert is_locked(vault_file) is False


def test_set_unlocked_returns_dict(vault_file):
    result = set_unlocked(vault_file)
    assert result["locked"] is False
    assert result["identity"] is None


def test_assert_unlocked_passes_when_not_locked(vault_file):
    # should not raise
    assert_unlocked(vault_file)


def test_assert_unlocked_raises_when_locked(vault_file):
    set_locked(vault_file, "charlie")
    with pytest.raises(RuntimeError, match="charlie"):
        assert_unlocked(vault_file)


def test_is_locked_false_by_default(vault_file):
    assert is_locked(vault_file) is False


def test_locked_at_is_iso_format(vault_file):
    result = set_locked(vault_file, "alice")
    ts = result["locked_at"]
    # basic ISO-8601 UTC check
    assert "T" in ts and ts.endswith("Z")
