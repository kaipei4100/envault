"""CLI tests for `envault blame run`."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.blame import BlameLine  # noqa: F401 – ensure importable
from envault.cli_blame import blame_group
from envault.crypto import encrypt
from envault.parser import serialise_env
from envault.vault import write_vault


PASSWORD = "cli-blame-pw"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vpath = tmp_path / "cli.vault"
    env = {"HOST": "localhost", "PORT": "5432"}
    raw = encrypt(serialise_env(env).encode(), PASSWORD)
    write_vault(vpath, raw, note="setup")
    return vpath


def test_blame_run_exits_zero(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(blame_group, ["run", str(vault_file), "--password", PASSWORD])
    assert result.exit_code == 0


def test_blame_run_lists_keys(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(blame_group, ["run", str(vault_file), "--password", PASSWORD])
    assert "HOST" in result.output
    assert "PORT" in result.output


def test_blame_run_hides_values_by_default(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(blame_group, ["run", str(vault_file), "--password", PASSWORD])
    assert "localhost" not in result.output


def test_blame_run_shows_values_with_flag(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        blame_group,
        ["run", str(vault_file), "--password", PASSWORD, "--show-values"],
    )
    assert "localhost" in result.output


def test_blame_run_filter_by_key(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        blame_group,
        ["run", str(vault_file), "--password", PASSWORD, "--key", "HOST"],
    )
    assert "HOST" in result.output
    assert "PORT" not in result.output


def test_blame_run_missing_key_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        blame_group,
        ["run", str(vault_file), "--password", PASSWORD, "--key", "NONEXISTENT"],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "")
