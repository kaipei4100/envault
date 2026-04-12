"""Tests for the hook CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.cli_hooks import hook_group
from envault.hooks import load_hooks


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_hook_set_creates_hook(runner, vault_dir):
    result = runner.invoke(
        hook_group, ["set", "post-lock", "echo locked", "--vault-dir", str(vault_dir)]
    )
    assert result.exit_code == 0
    assert "post-lock" in result.output
    hooks = load_hooks(vault_dir)
    assert hooks["post-lock"] == "echo locked"


def test_hook_set_invalid_event_fails(runner, vault_dir):
    result = runner.invoke(
        hook_group, ["set", "on-deploy", "make", "--vault-dir", str(vault_dir)]
    )
    assert result.exit_code != 0


def test_hook_unset_removes_hook(runner, vault_dir):
    runner.invoke(
        hook_group, ["set", "pre-push", "make lint", "--vault-dir", str(vault_dir)]
    )
    result = runner.invoke(
        hook_group, ["unset", "pre-push", "--vault-dir", str(vault_dir)]
    )
    assert result.exit_code == 0
    assert load_hooks(vault_dir).get("pre-push") is None


def test_hook_unset_missing_hook_is_graceful(runner, vault_dir):
    result = runner.invoke(
        hook_group, ["unset", "post-pull", "--vault-dir", str(vault_dir)]
    )
    assert result.exit_code == 0
    assert "No hook" in result.output


def test_hook_list_shows_hooks(runner, vault_dir):
    runner.invoke(
        hook_group, ["set", "post-lock", "echo hi", "--vault-dir", str(vault_dir)]
    )
    result = runner.invoke(hook_group, ["list", "--vault-dir", str(vault_dir)])
    assert result.exit_code == 0
    assert "post-lock" in result.output
    assert "echo hi" in result.output


def test_hook_list_empty_message(runner, vault_dir):
    result = runner.invoke(hook_group, ["list", "--vault-dir", str(vault_dir)])
    assert result.exit_code == 0
    assert "No hooks" in result.output
