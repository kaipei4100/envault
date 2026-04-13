"""CLI tests for envault.cli_checksum."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.checksum import _checksum_path, compute, save_checksum
from envault.cli_checksum import checksum_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "my.vault"
    vf.write_bytes(b"some-encrypted-bytes")
    return vf


def test_generate_creates_checksum_file(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(checksum_group, ["generate", str(vault_file)])
    assert result.exit_code == 0
    assert _checksum_path(vault_file).exists()


def test_generate_outputs_digest(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(checksum_group, ["generate", str(vault_file)])
    expected = compute(vault_file.read_bytes())
    assert expected in result.output


def test_verify_passes_for_unchanged_file(runner: CliRunner, vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    result = runner.invoke(checksum_group, ["verify", str(vault_file)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_verify_fails_for_tampered_file(runner: CliRunner, vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    vault_file.write_bytes(b"tampered")  # mutate after saving checksum
    result = runner.invoke(checksum_group, ["verify", str(vault_file)])
    assert result.exit_code != 0
    assert "FAIL" in result.output


def test_verify_warns_when_no_checksum_file(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(checksum_group, ["verify", str(vault_file)])
    assert result.exit_code != 0
    assert "No checksum file" in result.output


def test_show_displays_stored_digest(runner: CliRunner, vault_file: Path) -> None:
    save_checksum(vault_file, vault_file.read_bytes())
    result = runner.invoke(checksum_group, ["show", str(vault_file)])
    assert result.exit_code == 0
    assert "digest" in result.output
    assert "sha256" in result.output


def test_show_fails_when_no_checksum_file(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(checksum_group, ["show", str(vault_file)])
    assert result.exit_code != 0
