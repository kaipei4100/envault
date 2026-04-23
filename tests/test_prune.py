"""Tests for envault.prune."""
from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.vault import write_vault
from envault.snapshot import save_snapshot
from envault.prune import (
    PruneResult,
    get_prune_policy,
    prune,
    set_prune_policy,
    _prune_config_path,
)
from envault.cli_prune import prune_group

PASSWORD = "hunter2"
SAMPLE_ENV = {"KEY": "value", "OTHER": "data"}


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "test.vault"
    write_vault(vf, SAMPLE_ENV, PASSWORD)
    # Create three snapshots
    for _ in range(3):
        save_snapshot(vf, SAMPLE_ENV, PASSWORD)
    return vf


def test_prune_config_path_has_correct_suffix(vault_file: Path) -> None:
    assert _prune_config_path(vault_file).suffix == ".json"


def test_set_prune_policy_creates_file(vault_file: Path) -> None:
    set_prune_policy(vault_file, keep=2)
    assert _prune_config_path(vault_file).exists()


def test_set_prune_policy_returns_dict(vault_file: Path) -> None:
    result = set_prune_policy(vault_file, keep=3)
    assert result == {"keep": 3}


def test_set_prune_policy_invalid_keep_raises(vault_file: Path) -> None:
    with pytest.raises(ValueError):
        set_prune_policy(vault_file, keep=0)


def test_get_prune_policy_returns_none_when_missing(vault_file: Path) -> None:
    assert get_prune_policy(vault_file) is None


def test_get_prune_policy_roundtrip(vault_file: Path) -> None:
    set_prune_policy(vault_file, keep=5)
    policy = get_prune_policy(vault_file)
    assert policy is not None
    assert policy["keep"] == 5


def test_prune_returns_prune_result(vault_file: Path) -> None:
    result = prune(vault_file, keep=2)
    assert isinstance(result, PruneResult)


def test_prune_keeps_correct_number(vault_file: Path) -> None:
    result = prune(vault_file, keep=2)
    assert len(result.kept) == 2


def test_prune_removes_excess(vault_file: Path) -> None:
    result = prune(vault_file, keep=2)
    assert len(result.removed) == 1


def test_prune_result_ok(vault_file: Path) -> None:
    result = prune(vault_file, keep=1)
    assert result.ok is True


def test_prune_summary_string(vault_file: Path) -> None:
    result = prune(vault_file, keep=1)
    summary = result.summary()
    assert "Kept" in summary and "removed" in summary


def test_prune_invalid_keep_raises(vault_file: Path) -> None:
    with pytest.raises(ValueError):
        prune(vault_file, keep=0)


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_prune_run_exits_zero(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(prune_group, ["run", str(vault_file), "--keep", "2"])
    assert result.exit_code == 0


def test_cli_prune_policy_exits_zero(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(prune_group, ["policy", str(vault_file), "--keep", "3"])
    assert result.exit_code == 0
    assert "3" in result.output


def test_cli_prune_show_no_policy(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(prune_group, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "No prune policy" in result.output


def test_cli_prune_show_with_policy(runner: CliRunner, vault_file: Path) -> None:
    set_prune_policy(vault_file, keep=4)
    result = runner.invoke(prune_group, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "4" in result.output
