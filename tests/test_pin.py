"""Tests for envault.pin and envault.cli_pin."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.pin import (
    set_pin,
    get_pin,
    delete_pin,
    check_pin,
    PinViolation,
    _pin_path,
)
from envault.cli_pin import pin_group


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


# --- unit tests ---

def test_pin_path_has_pin_suffix(vault_file: Path) -> None:
    assert _pin_path(vault_file).suffix == ".pin"


def test_get_pin_returns_none_when_no_pin(vault_file: Path) -> None:
    assert get_pin(vault_file) is None


def test_set_pin_creates_pin_file(vault_file: Path) -> None:
    set_pin(vault_file, 3)
    assert _pin_path(vault_file).exists()


def test_get_pin_returns_correct_version(vault_file: Path) -> None:
    set_pin(vault_file, 5, note="stable release")
    info = get_pin(vault_file)
    assert info is not None
    assert info["version"] == 5
    assert info["note"] == "stable release"


def test_set_pin_invalid_version_raises(vault_file: Path) -> None:
    with pytest.raises(ValueError):
        set_pin(vault_file, 0)


def test_delete_pin_returns_true_when_pin_existed(vault_file: Path) -> None:
    set_pin(vault_file, 2)
    assert delete_pin(vault_file) is True


def test_delete_pin_returns_false_when_no_pin(vault_file: Path) -> None:
    assert delete_pin(vault_file) is False


def test_delete_pin_removes_file(vault_file: Path) -> None:
    set_pin(vault_file, 1)
    delete_pin(vault_file)
    assert get_pin(vault_file) is None


def test_check_pin_passes_when_no_pin(vault_file: Path) -> None:
    check_pin(vault_file, 99)  # should not raise


def test_check_pin_passes_for_matching_version(vault_file: Path) -> None:
    set_pin(vault_file, 4)
    check_pin(vault_file, 4)  # should not raise


def test_check_pin_raises_for_wrong_version(vault_file: Path) -> None:
    set_pin(vault_file, 4)
    with pytest.raises(PinViolation, match="pinned to version 4"):
        check_pin(vault_file, 5)


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_set_pin(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(pin_group, ["set", str(vault_file), "3"])
    assert result.exit_code == 0
    assert "version 3" in result.output


def test_cli_show_no_pin(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(pin_group, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "No pin set" in result.output


def test_cli_show_existing_pin(runner: CliRunner, vault_file: Path) -> None:
    set_pin(vault_file, 7, note="lts")
    result = runner.invoke(pin_group, ["show", str(vault_file)])
    assert "7" in result.output
    assert "lts" in result.output


def test_cli_delete_pin(runner: CliRunner, vault_file: Path) -> None:
    set_pin(vault_file, 2)
    result = runner.invoke(pin_group, ["delete", str(vault_file)])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_cli_delete_no_pin(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(pin_group, ["delete", str(vault_file)])
    assert result.exit_code == 0
    assert "No pin was set" in result.output
