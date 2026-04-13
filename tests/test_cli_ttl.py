"""Tests for the TTL CLI commands."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_ttl import ttl_group
from envault import ttl as ttl_mod


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    p.write_bytes(b"dummy")
    return p


def _iso_future(seconds: int = 3600) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _iso_past(seconds: int = 3600) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()


# ---------------------------------------------------------------------------
# ttl set
# ---------------------------------------------------------------------------

def test_set_creates_ttl(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(ttl_group, ["set", str(vault_file), "API_KEY", _iso_future()])
    assert result.exit_code == 0
    assert ttl_mod.get_ttl(vault_file, "API_KEY") is not None


def test_set_outputs_confirmation(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(ttl_group, ["set", str(vault_file), "TOKEN", _iso_future()])
    assert "TTL set" in result.output
    assert "TOKEN" in result.output


def test_set_invalid_date_fails(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(ttl_group, ["set", str(vault_file), "KEY", "not-a-date"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# ttl get
# ---------------------------------------------------------------------------

def test_get_shows_expiry(runner: CliRunner, vault_file: Path) -> None:
    expiry = _iso_future()
    runner.invoke(ttl_group, ["set", str(vault_file), "DB", expiry])
    result = runner.invoke(ttl_group, ["get", str(vault_file), "DB"])
    assert result.exit_code == 0
    assert "2025" in result.output or "+00:00" in result.output or "Z" in result.output


def test_get_missing_key_says_no_ttl(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(ttl_group, ["get", str(vault_file), "GHOST"])
    assert result.exit_code == 0
    assert "No TTL" in result.output


# ---------------------------------------------------------------------------
# ttl delete
# ---------------------------------------------------------------------------

def test_delete_removes_ttl(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(ttl_group, ["set", str(vault_file), "OLD", _iso_future()])
    result = runner.invoke(ttl_group, ["delete", str(vault_file), "OLD"])
    assert result.exit_code == 0
    assert ttl_mod.get_ttl(vault_file, "OLD") is None


def test_delete_missing_key_says_not_found(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(ttl_group, ["delete", str(vault_file), "NOPE"])
    assert "No TTL found" in result.output


# ---------------------------------------------------------------------------
# ttl list
# ---------------------------------------------------------------------------

def test_list_shows_all_keys(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(ttl_group, ["set", str(vault_file), "A", _iso_future(100)])
    runner.invoke(ttl_group, ["set", str(vault_file), "B", _iso_future(200)])
    result = runner.invoke(ttl_group, ["list", str(vault_file)])
    assert "A" in result.output
    assert "B" in result.output


def test_list_empty_vault_says_none(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(ttl_group, ["list", str(vault_file)])
    assert "No TTLs" in result.output


# ---------------------------------------------------------------------------
# ttl check
# ---------------------------------------------------------------------------

def test_check_reports_expired(runner: CliRunner, vault_file: Path) -> None:
    ttl_mod.set_ttl(vault_file, "STALE",
                    datetime.now(timezone.utc) - timedelta(hours=1))
    result = runner.invoke(ttl_group, ["check", str(vault_file)])
    assert "STALE" in result.output
    assert "Expired" in result.output


def test_check_all_ok_message(runner: CliRunner, vault_file: Path) -> None:
    ttl_mod.set_ttl(vault_file, "FRESH",
                    datetime.now(timezone.utc) + timedelta(days=30))
    result = runner.invoke(
        ttl_group, ["check", str(vault_file), "--warn-within", "3600"]
    )
    assert "within their TTL" in result.output
