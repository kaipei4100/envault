"""Tests for envault.audit — audit log recording and retrieval."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import (
    AUDIT_FILENAME,
    _audit_path,
    format_events,
    read_events,
    record_event,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / "vault"


def test_audit_path_returns_correct_file(vault_dir: Path) -> None:
    expected = vault_dir / AUDIT_FILENAME
    assert _audit_path(vault_dir) == expected


def test_record_event_creates_log_file(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", version=1)
    assert _audit_path(vault_dir).exists()


def test_record_event_returns_dict_with_expected_keys(vault_dir: Path) -> None:
    event = record_event(vault_dir, "lock", version=1, user="alice")
    assert "timestamp" in event
    assert event["action"] == "lock"
    assert event["version"] == 1
    assert event["user"] == "alice"


def test_record_event_note_included_when_provided(vault_dir: Path) -> None:
    event = record_event(vault_dir, "push", version=2, note="deploy v2")
    assert event["note"] == "deploy v2"


def test_record_event_note_absent_when_not_provided(vault_dir: Path) -> None:
    event = record_event(vault_dir, "pull", version=1)
    assert "note" not in event


def test_record_event_appends_valid_jsonl(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", version=1, user="bob")
    record_event(vault_dir, "unlock", version=1, user="bob")
    lines = _audit_path(vault_dir).read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "action" in obj


def test_read_events_returns_empty_list_when_no_log(vault_dir: Path) -> None:
    assert read_events(vault_dir) == []


def test_read_events_returns_all_events_in_order(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", version=1)
    record_event(vault_dir, "push", version=2)
    events = read_events(vault_dir)
    assert len(events) == 2
    assert events[0]["action"] == "lock"
    assert events[1]["action"] == "push"


def test_format_events_no_events_message(vault_dir: Path) -> None:
    output = format_events([])
    assert "No audit events" in output


def test_format_events_contains_action_and_version(vault_dir: Path) -> None:
    record_event(vault_dir, "unlock", version=3, user="carol")
    events = read_events(vault_dir)
    output = format_events(events)
    assert "unlock" in output
    assert "3" in output
    assert "carol" in output
