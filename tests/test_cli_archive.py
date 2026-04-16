"""Tests for envault.cli_archive."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import write_vault
from envault.snapshot import save_snapshot
from envault.cli_archive import archive_group

PASSWORD = "testpass"
ENV = {"A": "1", "B": "2"}


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    write_vault(vf, ENV, PASSWORD)
    for _ in range(5):
        save_snapshot(vf, ENV, PASSWORD)
    return vf


def test_archive_create_exits_zero(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(archive_group, ["create", str(vault_file), "--password", PASSWORD, "--keep", "3"])
    assert result.exit_code == 0


def test_archive_create_reports_versions(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(archive_group, ["create", str(vault_file), "--password", PASSWORD, "--keep", "3"])
    assert "Archived versions" in result.output


def test_archive_create_nothing_to_do(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(archive_group, ["create", str(vault_file), "--password", PASSWORD, "--keep", "99"])
    assert "Nothing to archive" in result.output


def test_archive_list_empty(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(archive_group, ["list", str(vault_file)])
    assert result.exit_code == 0
    assert "empty" in result.output.lower() or result.output.strip() == "Archive is empty or does not exist."


def test_archive_list_shows_versions(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(archive_group, ["create", str(vault_file), "--password", PASSWORD, "--keep", "3"])
    result = runner.invoke(archive_group, ["list", str(vault_file)])
    assert "v" in result.output


def test_archive_restore_exits_zero(runner: CliRunner, vault_file: Path) -> None:
    create_result = runner.invoke(archive_group, ["create", str(vault_file), "--password", PASSWORD, "--keep", "3"])
    list_result = runner.invoke(archive_group, ["list", str(vault_file)])
    # extract first version from list output
    lines = [l.strip() for l in list_result.output.splitlines() if l.strip().startswith("v")]
    version = int(lines[0][1:])
    result = runner.invoke(archive_group, ["restore", str(vault_file), str(version)])
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_archive_restore_bad_version_fails(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(archive_group, ["create", str(vault_file), "--password", PASSWORD, "--keep", "3"])
    result = runner.invoke(archive_group, ["restore", str(vault_file), "9999"])
    assert result.exit_code != 0
