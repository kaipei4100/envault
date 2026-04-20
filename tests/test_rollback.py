"""Tests for envault.rollback."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import write_vault
from envault.snapshot import save_snapshot
from envault.rollback import rollback, can_rollback, RollbackError


PASSWORD = "rollback-secret"

ENV_V1 = {"APP": "alpha", "DB": "postgres"}
ENV_V2 = {"APP": "beta", "DB": "postgres", "CACHE": "redis"}


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    write_vault(path, PASSWORD, ENV_V1)
    save_snapshot(path, PASSWORD, ENV_V1)  # snapshot v1
    write_vault(path, PASSWORD, ENV_V2)
    save_snapshot(path, PASSWORD, ENV_V2)  # snapshot v2
    return path


def test_rollback_returns_rollback_result(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    assert result is not None


def test_rollback_from_version_is_current_before_rollback(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    assert result.from_version == 2


def test_rollback_to_version_matches_target(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    assert result.to_version == 1


def test_rollback_new_version_is_incremented(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    assert result.new_version == 3


def test_rollback_keys_restored_count(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    assert result.keys_restored == len(ENV_V1)


def test_rollback_restores_env_content(vault_file: Path):
    from envault.vault import read_vault

    rollback(vault_file, PASSWORD, target_version=1)
    env = read_vault(vault_file, PASSWORD)
    assert env == ENV_V1


def test_rollback_audit_event_has_correct_type(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    assert result.audit["event"] == "rollback"


def test_rollback_audit_contains_version_info(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1)
    extra = result.audit.get("extra", {})
    assert extra["to_version"] == 1
    assert extra["from_version"] == 2


def test_rollback_invalid_version_raises(vault_file: Path):
    with pytest.raises(RollbackError, match="not found"):
        rollback(vault_file, PASSWORD, target_version=99)


def test_rollback_wrong_password_raises(vault_file: Path):
    with pytest.raises(Exception):
        rollback(vault_file, "wrong-password", target_version=1)


def test_rollback_custom_note_stored(vault_file: Path):
    result = rollback(vault_file, PASSWORD, target_version=1, note="emergency fix")
    assert "emergency fix" in result.audit.get("note", "")


def test_can_rollback_true_when_multiple_snapshots(vault_file: Path):
    assert can_rollback(vault_file) is True


def test_can_rollback_false_when_single_snapshot(tmp_path: Path):
    path = tmp_path / "single.vault"
    write_vault(path, PASSWORD, ENV_V1)
    save_snapshot(path, PASSWORD, ENV_V1)
    assert can_rollback(path) is False
