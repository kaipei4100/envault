"""Tests for envault.remind."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from envault.remind import (
    _remind_path,
    set_reminder,
    get_reminder,
    delete_reminder,
    check_reminder,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_bytes(b"dummy")
    return p


def test_remind_path_has_correct_suffix(vault_file):
    assert _remind_path(vault_file).suffix == ".json"
    assert ".remind" in _remind_path(vault_file).name


def test_remind_path_sibling_of_vault(vault_file):
    assert _remind_path(vault_file).parent == vault_file.parent


def test_get_reminder_returns_none_when_missing(vault_file):
    assert get_reminder(vault_file) is None


def test_set_reminder_persists(vault_file):
    set_reminder(vault_file, 30)
    assert get_reminder(vault_file) == 30


def test_set_reminder_returns_dict(vault_file):
    result = set_reminder(vault_file, 14)
    assert result == {"max_age_days": 14}


def test_set_reminder_overwrites(vault_file):
    set_reminder(vault_file, 30)
    set_reminder(vault_file, 7)
    assert get_reminder(vault_file) == 7


def test_set_reminder_invalid_raises(vault_file):
    with pytest.raises(ValueError):
        set_reminder(vault_file, 0)


def test_delete_reminder_removes_file(vault_file):
    set_reminder(vault_file, 30)
    delete_reminder(vault_file)
    assert get_reminder(vault_file) is None


def test_delete_reminder_noop_when_missing(vault_file):
    delete_reminder(vault_file)  # should not raise


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def test_check_reminder_not_due(vault_file):
    set_reminder(vault_file, 30)
    recent = datetime.now(tz=timezone.utc) - timedelta(days=5)
    result = check_reminder(vault_file, _iso(recent))
    assert result["due"] is False
    assert result["age_days"] == 5


def test_check_reminder_due(vault_file):
    set_reminder(vault_file, 30)
    old = datetime.now(tz=timezone.utc) - timedelta(days=31)
    result = check_reminder(vault_file, _iso(old))
    assert result["due"] is True


def test_check_reminder_no_policy_never_due(vault_file):
    old = datetime.now(tz=timezone.utc) - timedelta(days=365)
    result = check_reminder(vault_file, _iso(old))
    assert result["due"] is False
    assert result["max_age_days"] is None
