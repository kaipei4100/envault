"""Tests for envault.rotate."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.crypto import encrypt, decrypt, fingerprint
from envault.vault import write_vault, vault_metadata
from envault.rotate import rotate_key, rotation_needed


OLD_PASSWORD = "old-secret"
NEW_PASSWORD = "new-secret"
PLAINTEXT = b"API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """Create a minimal vault encrypted with OLD_PASSWORD."""
    path = tmp_path / "test.vault"
    ciphertext = encrypt(PLAINTEXT, OLD_PASSWORD)
    write_vault(path, ciphertext)
    return path


def test_rotate_key_returns_audit_event(vault_file):
    event = rotate_key(vault_file, OLD_PASSWORD, NEW_PASSWORD)
    assert event["action"] == "rotate"


def test_rotate_key_new_password_decrypts(vault_file):
    rotate_key(vault_file, OLD_PASSWORD, NEW_PASSWORD)
    ciphertext = vault_file.read_bytes()
    recovered = decrypt(ciphertext, NEW_PASSWORD)
    assert recovered == PLAINTEXT


def test_rotate_key_old_password_no_longer_works(vault_file):
    rotate_key(vault_file, OLD_PASSWORD, NEW_PASSWORD)
    ciphertext = vault_file.read_bytes()
    with pytest.raises(Exception):
        decrypt(ciphertext, OLD_PASSWORD)


def test_rotate_key_bumps_version(vault_file):
    meta_before = vault_metadata(vault_file)
    rotate_key(vault_file, OLD_PASSWORD, NEW_PASSWORD)
    meta_after = vault_metadata(vault_file)
    assert meta_after["version"] > meta_before["version"]


def test_rotate_key_wrong_old_password_raises(vault_file):
    with pytest.raises(Exception):
        rotate_key(vault_file, "wrong-password", NEW_PASSWORD)


def test_rotate_key_missing_vault_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        rotate_key(tmp_path / "nonexistent.vault", OLD_PASSWORD, NEW_PASSWORD)


def test_rotate_key_note_in_audit_event(vault_file):
    event = rotate_key(vault_file, OLD_PASSWORD, NEW_PASSWORD, note="quarterly rotation")
    assert event.get("note") == "quarterly rotation"


def test_rotation_needed_false_when_fingerprints_match(vault_file):
    fp = fingerprint(OLD_PASSWORD)
    # Manually patch meta to hold the fingerprint
    from envault.vault import _meta_path
    import json
    meta_path = _meta_path(vault_file)
    meta = json.loads(meta_path.read_text())
    meta["fingerprint"] = fp
    meta_path.write_text(json.dumps(meta))
    assert rotation_needed(vault_file, OLD_PASSWORD, fp) is False


def test_rotation_needed_true_when_fingerprints_differ(vault_file):
    from envault.vault import _meta_path
    import json
    meta_path = _meta_path(vault_file)
    meta = json.loads(meta_path.read_text())
    meta["fingerprint"] = fingerprint(NEW_PASSWORD)
    meta_path.write_text(json.dumps(meta))
    assert rotation_needed(vault_file, OLD_PASSWORD, fingerprint(OLD_PASSWORD)) is True
