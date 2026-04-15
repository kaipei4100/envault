"""Tests for envault.schedule."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.schedule import (
    InvalidCronExpression,
    _schedule_path,
    delete_schedule,
    get_schedule,
    rotation_overdue,
    set_schedule,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "project" / "secrets.vault"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"dummy")
    return p


# ---------------------------------------------------------------------------
# _schedule_path
# ---------------------------------------------------------------------------

def test_schedule_path_has_correct_suffix(vault_file: Path) -> None:
    p = _schedule_path(vault_file)
    assert p.name.endswith(".schedule.json")


def test_schedule_path_sibling_of_vault(vault_file: Path) -> None:
    p = _schedule_path(vault_file)
    assert p.parent == vault_file.parent


# ---------------------------------------------------------------------------
# set_schedule
# ---------------------------------------------------------------------------

def test_set_schedule_creates_file(vault_file: Path) -> None:
    set_schedule(vault_file, "0 0 * * *")
    assert _schedule_path(vault_file).exists()


def test_set_schedule_returns_dict_with_cron(vault_file: Path) -> None:
    record = set_schedule(vault_file, "0 6 * * 1")
    assert record["cron"] == "0 6 * * 1"


def test_set_schedule_stores_note(vault_file: Path) -> None:
    record = set_schedule(vault_file, "0 0 * * *", note="weekly rotation")
    assert record["note"] == "weekly rotation"


def test_set_schedule_persists_to_disk(vault_file: Path) -> None:
    set_schedule(vault_file, "0 0 1 * *", note="monthly")
    raw = json.loads(_schedule_path(vault_file).read_text())
    assert raw["cron"] == "0 0 1 * *"
    assert raw["note"] == "monthly"


def test_set_schedule_invalid_cron_raises(vault_file: Path) -> None:
    with pytest.raises(InvalidCronExpression):
        set_schedule(vault_file, "not-a-cron")


def test_set_schedule_too_few_fields_raises(vault_file: Path) -> None:
    with pytest.raises(InvalidCronExpression):
        set_schedule(vault_file, "0 0 * *")


# ---------------------------------------------------------------------------
# get_schedule
# ---------------------------------------------------------------------------

def test_get_schedule_returns_none_when_missing(vault_file: Path) -> None:
    assert get_schedule(vault_file) is None


def test_get_schedule_returns_stored_record(vault_file: Path) -> None:
    set_schedule(vault_file, "0 12 * * *")
    s = get_schedule(vault_file)
    assert s is not None
    assert s["cron"] == "0 12 * * *"


# ---------------------------------------------------------------------------
# delete_schedule
# ---------------------------------------------------------------------------

def test_delete_schedule_removes_file(vault_file: Path) -> None:
    set_schedule(vault_file, "0 0 * * 0")
    assert delete_schedule(vault_file) is True
    assert not _schedule_path(vault_file).exists()


def test_delete_schedule_returns_false_when_no_file(vault_file: Path) -> None:
    assert delete_schedule(vault_file) is False


# ---------------------------------------------------------------------------
# rotation_overdue
# ---------------------------------------------------------------------------

def _iso_ago(hours: float) -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt.isoformat()


def test_rotation_not_overdue_when_no_schedule(vault_file: Path) -> None:
    assert rotation_overdue(vault_file, _iso_ago(100)) is False


def test_rotation_not_overdue_when_no_last_rotated(vault_file: Path) -> None:
    set_schedule(vault_file, "0 0 * * *")
    assert rotation_overdue(vault_file, None) is False


def test_daily_schedule_overdue(vault_file: Path) -> None:
    set_schedule(vault_file, "0 0 * * *")
    assert rotation_overdue(vault_file, _iso_ago(25)) is True


def test_daily_schedule_not_overdue(vault_file: Path) -> None:
    set_schedule(vault_file, "0 0 * * *")
    assert rotation_overdue(vault_file, _iso_ago(12)) is False


def test_weekly_alias_overdue(vault_file: Path) -> None:
    set_schedule(vault_file, "@weekly")
    assert rotation_overdue(vault_file, _iso_ago(170)) is True


def test_monthly_alias_not_overdue(vault_file: Path) -> None:
    set_schedule(vault_file, "@monthly")
    assert rotation_overdue(vault_file, _iso_ago(48)) is False
