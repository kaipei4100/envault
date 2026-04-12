"""Tests for envault.import_env."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.import_env import import_env_file, preview_import
from envault.vault import read_vault
from envault.parser import parse_env


PASSWORD = "import-test-secret"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_ENV=production\nDB_URL=postgres://localhost/db\nDEBUG=false\n")
    return p


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "vault"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# import_env_file
# ---------------------------------------------------------------------------

def test_import_creates_vault_file(env_file, vault_dir):
    import_env_file(env_file, vault_dir, PASSWORD)
    vault_file = vault_dir / "vault.enc"
    assert vault_file.exists()


def test_import_returns_audit_event(env_file, vault_dir):
    event = import_env_file(env_file, vault_dir, PASSWORD)
    assert event["action"] == "import"
    assert "timestamp" in event
    assert event["version"] == 1


def test_import_note_stored_in_event(env_file, vault_dir):
    event = import_env_file(env_file, vault_dir, PASSWORD, note="initial import")
    assert event["note"] == "initial import"


def test_import_default_note_contains_filename(env_file, vault_dir):
    event = import_env_file(env_file, vault_dir, PASSWORD)
    assert ".env" in event["note"]


def test_import_data_decryptable(env_file, vault_dir):
    import_env_file(env_file, vault_dir, PASSWORD)
    plaintext = read_vault(vault_dir, PASSWORD)
    pairs = parse_env(plaintext.decode())
    assert pairs["APP_ENV"] == "production"
    assert pairs["DB_URL"] == "postgres://localhost/db"


def test_import_missing_file_raises(vault_dir):
    with pytest.raises(FileNotFoundError):
        import_env_file(vault_dir / "nonexistent.env", vault_dir, PASSWORD)


def test_import_empty_file_raises(tmp_path, vault_dir):
    empty = tmp_path / "empty.env"
    empty.write_text("# just a comment\n")
    with pytest.raises(ValueError):
        import_env_file(empty, vault_dir, PASSWORD)


# ---------------------------------------------------------------------------
# preview_import
# ---------------------------------------------------------------------------

def test_preview_returns_dict(env_file):
    pairs = preview_import(env_file)
    assert isinstance(pairs, dict)
    assert pairs["DEBUG"] == "false"


def test_preview_does_not_write_vault(env_file, vault_dir):
    preview_import(env_file)
    assert not (vault_dir / "vault.enc").exists()


def test_preview_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        preview_import(tmp_path / "ghost.env")
