"""Tests for envault.cli_lock_status."""
from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli_lock_status import lock_status_group
from envault.lock_status import set_locked


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_bytes(b"dummy")
    return p


def test_show_unlocked_vault(runner, vault_file):
    result = runner.invoke(lock_status_group, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "unlocked" in result.output.lower()


def test_lock_sets_locked_status(runner, vault_file):
    result = runner.invoke(
        lock_status_group, ["lock", str(vault_file), "--identity", "alice"]
    )
    assert result.exit_code == 0
    assert "alice" in result.output


def test_lock_with_note_accepted(runner, vault_file):
    result = runner.invoke(
        lock_status_group,
        ["lock", str(vault_file), "--identity", "alice", "--note", "scheduled"],
    )
    assert result.exit_code == 0


def test_show_locked_vault_displays_identity(runner, vault_file):
    set_locked(str(vault_file), "bob", note="maintenance")
    result = runner.invoke(lock_status_group, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "bob" in result.output
    assert "LOCKED" in result.output


def test_show_locked_vault_displays_note(runner, vault_file):
    set_locked(str(vault_file), "bob", note="maintenance")
    result = runner.invoke(lock_status_group, ["show", str(vault_file)])
    assert "maintenance" in result.output


def test_lock_already_locked_exits_nonzero(runner, vault_file):
    set_locked(str(vault_file), "alice")
    result = runner.invoke(
        lock_status_group, ["lock", str(vault_file), "--identity", "bob"]
    )
    assert result.exit_code != 0


def test_unlock_removes_lock(runner, vault_file):
    set_locked(str(vault_file), "alice")
    result = runner.invoke(lock_status_group, ["unlock", str(vault_file)])
    assert result.exit_code == 0
    assert "unlocked" in result.output.lower()


def test_unlock_already_unlocked_is_graceful(runner, vault_file):
    result = runner.invoke(lock_status_group, ["unlock", str(vault_file)])
    assert result.exit_code == 0
    assert "not locked" in result.output.lower()
