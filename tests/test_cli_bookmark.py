"""Tests for envault.cli_bookmark."""
from __future__ import annotations

importfrom click.testing import CliRunner

from envault.cli_bookmark import bookmark_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


def test_bookmark_set_exits_zero(runner, vault_file):
    result = runner.invoke(bookmark_group, ["set", str(vault_file), "stable", "3"])
    assert result.exit_code == 0


def test_bookmark_set_output_contains_label(runner, vault_file):
    result = runner.invoke(bookmark_group, ["set", str(vault_file), "stable", "3"])
    assert "stable" in result.output


def test_bookmark_set_output_contains_version(runner, vault_file):
    result = runner.invoke(bookmark_group, ["set", str(vault_file), "stable", "3"])
    assert "3" in result.output


def test_bookmark_get_returns_version(runner, vault_file):
    runner.invoke(bookmark_group, ["set", str(vault_file), "rel", "7"])
    result = runner.invoke(bookmark_group, ["get", str(vault_file), "rel"])
    assert result.exit_code == 0
    assert "7" in result.output


def test_bookmark_get_missing_label_fails(runner, vault_file):
    result = runner.invoke(bookmark_group, ["get", str(vault_file), "ghost"])
    assert result.exit_code != 0


def test_bookmark_delete_exits_zero(runner, vault_file):
    runner.invoke(bookmark_group, ["set", str(vault_file), "old", "1"])
    result = runner.invoke(bookmark_group, ["delete", str(vault_file), "old"])
    assert result.exit_code == 0


def test_bookmark_delete_output_confirms_label(runner, vault_file):
    runner.invoke(bookmark_group, ["set", str(vault_file), "old", "1"])
    result = runner.invoke(bookmark_group, ["delete", str(vault_file), "old"])
    assert "old" in result.output


def test_bookmark_delete_missing_fails(runner, vault_file):
    result = runner.invoke(bookmark_group, ["delete", str(vault_file), "nope"])
    assert result.exit_code != 0


def test_bookmark_list_empty_message(runner, vault_file):
    result = runner.invoke(bookmark_group, ["list", str(vault_file)])
    assert result.exit_code == 0
    assert "No bookmarks" in result.output


def test_bookmark_list_shows_all_labels(runner, vault_file):
    runner.invoke(bookmark_group, ["set", str(vault_file), "alpha", "1"])
    runner.invoke(bookmark_group, ["set", str(vault_file), "beta", "2"])
    result = runner.invoke(bookmark_group, ["list", str(vault_file)])
    assert "alpha" in result.output
    assert "beta" in result.output
