"""Tests for envault.blame."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.blame import BlameLine, blame, format_blame
from envault.crypto import encrypt
from envault.parser import serialise_env
from envault.vault import write_vault


PASSWORD = "blame-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """Create a vault with two versions so blame has history to inspect."""
    vpath = tmp_path / "test.vault"

    env_v1 = {"APP": "hello", "DEBUG": "false"}
    raw_v1 = encrypt(serialise_env(env_v1).encode(), PASSWORD)
    write_vault(vpath, raw_v1, note="initial import")

    env_v2 = {"APP": "world", "DEBUG": "false", "NEW_KEY": "added"}
    raw_v2 = encrypt(serialise_env(env_v2).encode(), PASSWORD)
    write_vault(vpath, raw_v2, note="update APP and add NEW_KEY")

    return vpath


def test_blame_returns_list_of_blame_lines(vault_file: Path) -> None:
    result = blame(vault_file, PASSWORD)
    assert isinstance(result, list)
    assert all(isinstance(b, BlameLine) for b in result)


def test_blame_covers_all_current_keys(vault_file: Path) -> None:
    result = blame(vault_file, PASSWORD)
    keys = {b.key for b in result}
    assert keys == {"APP", "DEBUG", "NEW_KEY"}


def test_blame_unchanged_key_attributed_to_first_version(vault_file: Path) -> None:
    result = blame(vault_file, PASSWORD)
    debug_line = next(b for b in result if b.key == "DEBUG")
    assert debug_line.version == 1


def test_blame_changed_key_attributed_to_later_version(vault_file: Path) -> None:
    result = blame(vault_file, PASSWORD)
    app_line = next(b for b in result if b.key == "APP")
    assert app_line.version == 2


def test_blame_new_key_attributed_to_version_it_appeared(vault_file: Path) -> None:
    result = blame(vault_file, PASSWORD)
    new_line = next(b for b in result if b.key == "NEW_KEY")
    assert new_line.version == 2


def test_blame_sorted_alphabetically(vault_file: Path) -> None:
    result = blame(vault_file, PASSWORD)
    keys = [b.key for b in result]
    assert keys == sorted(keys)


def test_format_blame_returns_string(vault_file: Path) -> None:
    lines = blame(vault_file, PASSWORD)
    out = format_blame(lines)
    assert isinstance(out, str)
    assert "APP" in out
    assert "DEBUG" in out


def test_format_blame_hides_values_by_default(vault_file: Path) -> None:
    lines = blame(vault_file, PASSWORD)
    out = format_blame(lines, show_values=False)
    assert "world" not in out


def test_format_blame_shows_values_when_requested(vault_file: Path) -> None:
    lines = blame(vault_file, PASSWORD)
    out = format_blame(lines, show_values=True)
    assert "world" in out


def test_format_blame_empty_returns_placeholder() -> None:
    out = format_blame([])
    assert "no keys" in out
