"""Tests for envault.replay."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import write_vault
from envault.snapshot import save_snapshot
from envault.replay import list_replayable, replay_to_version, ReplayError


PASSWORD = "replay-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    write_vault(path, {"KEY": "v1"}, PASSWORD)
    save_snapshot(path, PASSWORD)
    write_vault(path, {"KEY": "v2"}, PASSWORD)
    save_snapshot(path, PASSWORD)
    return path


def test_list_replayable_returns_list(vault_file: Path):
    items = list_replayable(vault_file)
    assert isinstance(items, list)


def test_list_replayable_contains_snapshot_versions(vault_file: Path):
    items = list_replayable(vault_file)
    versions = [i["version"] for i in items]
    assert 1 in versions or 2 in versions


def test_list_replayable_entries_have_expected_keys(vault_file: Path):
    items = list_replayable(vault_file)
    for item in items:
        assert "version" in item
        assert "action" in item


def test_replay_to_version_returns_dict(vault_file: Path):
    result = replay_to_version(vault_file, 1, PASSWORD)
    assert isinstance(result, dict)


def test_replay_event_action_is_replay(vault_file: Path):
    result = replay_to_version(vault_file, 1, PASSWORD)
    assert result["action"] == "replay"


def test_replay_event_records_replayed_from(vault_file: Path):
    result = replay_to_version(vault_file, 1, PASSWORD)
    assert result["replayed_from"] == 1


def test_replay_event_note_included_when_provided(vault_file: Path):
    result = replay_to_version(vault_file, 1, PASSWORD, note="rollback")
    assert result["note"] == "rollback"


def test_replay_event_note_absent_when_not_provided(vault_file: Path):
    result = replay_to_version(vault_file, 1, PASSWORD)
    assert "note" not in result


def test_replay_missing_version_raises(vault_file: Path):
    with pytest.raises(ReplayError):
        replay_to_version(vault_file, 999, PASSWORD)


def test_replay_wrong_password_raises(vault_file: Path):
    with pytest.raises(Exception):
        replay_to_version(vault_file, 1, "wrong-password")


def test_replay_bumps_vault_version(vault_file: Path):
    from envault.vault import vault_metadata
    before = vault_metadata(vault_file)["version"]
    replay_to_version(vault_file, 1, PASSWORD)
    after = vault_metadata(vault_file)["version"]
    assert after == before + 1
