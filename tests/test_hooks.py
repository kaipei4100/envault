"""Tests for envault.hooks."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.hooks import load_hooks, save_hooks, run_hook, HOOKS_FILE


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_hooks_missing_file_returns_empty(vault_dir):
    assert load_hooks(vault_dir) == {}


def test_save_and_load_hooks_roundtrip(vault_dir):
    hooks = {"post-lock": "echo locked", "pre-push": "make lint"}
    save_hooks(vault_dir, hooks)
    loaded = load_hooks(vault_dir)
    assert loaded == hooks


def test_save_hooks_creates_file(vault_dir):
    save_hooks(vault_dir, {"post-unlock": "echo done"})
    assert (vault_dir / HOOKS_FILE).exists()


def test_load_hooks_ignores_comments_and_blanks(vault_dir):
    (vault_dir / HOOKS_FILE).write_text(
        "# this is a comment\n\npost-lock=echo hi\n"
    )
    assert load_hooks(vault_dir) == {"post-lock": "echo hi"}


def test_load_hooks_ignores_unknown_events(vault_dir):
    (vault_dir / HOOKS_FILE).write_text("on-deploy=echo nope\npost-lock=echo yes\n")
    assert load_hooks(vault_dir) == {"post-lock": "echo yes"}


def test_save_hooks_raises_on_invalid_event(vault_dir):
    with pytest.raises(ValueError, match="Unknown hook event"):
        save_hooks(vault_dir, {"on-deploy": "echo bad"})


def test_run_hook_returns_none_when_no_hook(vault_dir):
    assert run_hook(vault_dir, "post-lock") is None


def test_run_hook_returns_exit_code(vault_dir):
    save_hooks(vault_dir, {"post-lock": "exit 0"})
    code = run_hook(vault_dir, "post-lock")
    assert code == 0


def test_run_hook_nonzero_exit_code_returned(vault_dir):
    save_hooks(vault_dir, {"post-lock": "exit 42"})
    code = run_hook(vault_dir, "post-lock")
    assert code == 42


def test_run_hook_passes_extra_env(vault_dir, monkeypatch):
    monkeypatch.delenv("_ENVAULT_TEST_VAR", raising=False)
    save_hooks(vault_dir, {"post-push": "test -n \"$_ENVAULT_TEST_VAR\""})
    code = run_hook(vault_dir, "post-push", env={"_ENVAULT_TEST_VAR": "hello"})
    assert code == 0


def test_run_hook_raises_on_unknown_event(vault_dir):
    """run_hook should raise ValueError when given an unrecognised event name."""
    with pytest.raises(ValueError, match="Unknown hook event"):
        run_hook(vault_dir, "on-deploy")
