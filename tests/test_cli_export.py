"""Integration tests for the 'envault export print' CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_export import export_group
from envault.crypto import encrypt
from envault.vault import write_vault

PASSWORD = "test-export-pw"
ENV_CONTENT = "API_KEY=abc123\nDEBUG=true\nSECRET=hello world\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    ciphertext = encrypt(ENV_CONTENT.encode(), PASSWORD)
    write_vault(path, ciphertext)
    return path


def test_export_shell_default(vault_file: Path):
    runner = CliRunner()
    result = runner.invoke(
        export_group, ["print", str(vault_file), "--password", PASSWORD]
    )
    assert result.exit_code == 0
    assert "export API_KEY=" in result.output
    assert "export DEBUG=" in result.output


def test_export_shell_no_export_flag(vault_file: Path):
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["print", str(vault_file), "--format", "shell", "--no-export", "--password", PASSWORD],
    )
    assert result.exit_code == 0
    for line in result.output.splitlines():
        assert not line.startswith("export ")


def test_export_docker_format(vault_file: Path):
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["print", str(vault_file), "--format", "docker", "--password", PASSWORD],
    )
    assert result.exit_code == 0
    for line in result.output.splitlines():
        assert line.startswith("--env ")


def test_export_json_format(vault_file: Path):
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["print", str(vault_file), "--format", "json", "--password", PASSWORD],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["API_KEY"] == "abc123"
    assert parsed["DEBUG"] == "true"


def test_export_wrong_password_exits_nonzero(vault_file: Path):
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["print", str(vault_file), "--password", "wrong"],
    )
    assert result.exit_code != 0


def test_export_to_file(vault_file: Path, tmp_path: Path):
    out_file = tmp_path / "out.sh"
    runner = CliRunner()
    result = runner.invoke(
        export_group,
        ["print", str(vault_file), "--output", str(out_file), "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "export API_KEY=" in content
