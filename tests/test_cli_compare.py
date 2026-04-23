"""CLI tests for envault compare."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_compare import compare_group
from envault.vault import write_vault
from envault.snapshot import save_snapshot


PASSWORD = "cli-compare-pw"


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_file(tmp_path):
    vf = tmp_path / "cli.vault"
    write_vault(str(vf), {"A": "1", "B": "old"}, PASSWORD)
    save_snapshot(str(vf), PASSWORD, version=1)
    write_vault(str(vf), {"A": "1", "B": "new", "C": "added"}, PASSWORD)
    save_snapshot(str(vf), PASSWORD, version=2)
    return str(vf)


def test_compare_run_exits_zero(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "2", "--password", PASSWORD],
    )
    assert result.exit_code == 0, result.output


def test_compare_run_shows_version_header(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "2", "--password", PASSWORD],
    )
    assert "v1" in result.output
    assert "v2" in result.output


def test_compare_run_reports_added_key(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "2", "--password", PASSWORD],
    )
    assert "C" in result.output


def test_compare_run_reports_changed_key(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "2", "--password", PASSWORD],
    )
    assert "B" in result.output


def test_compare_run_summary_line_present(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "2", "--password", PASSWORD],
    )
    assert "Summary:" in result.output


def test_compare_identical_versions_says_identical(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "1", "--password", PASSWORD],
    )
    assert "identical" in result.output.lower()


def test_compare_show_unchanged_flag(runner, vault_file):
    result = runner.invoke(
        compare_group,
        ["run", vault_file, "1", "2", "--password", PASSWORD, "--show-unchanged"],
    )
    assert "A" in result.output
    assert result.exit_code == 0
