"""Tests for envault.signing."""
from __future__ import annotations

import json

import pytest

from envault.signing import (
    SignatureError,
    _sig_path,
    sign_vault,
    signature_exists,
    verify_vault,
)

SECRET = "super-secret-key"


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "vault.env.enc"
    p.write_bytes(b"encrypted-content-here")
    return p


# ---------------------------------------------------------------------------
# _sig_path
# ---------------------------------------------------------------------------

def test_sig_path_appends_sig_suffix(vault_file):
    sig = _sig_path(vault_file)
    assert sig.name == "vault.env.enc.sig"


# ---------------------------------------------------------------------------
# sign_vault
# ---------------------------------------------------------------------------

def test_sign_vault_creates_sig_file(vault_file):
    sign_vault(vault_file, SECRET)
    assert _sig_path(vault_file).exists()


def test_sign_vault_returns_sig_path(vault_file):
    result = sign_vault(vault_file, SECRET)
    assert result == _sig_path(vault_file)


def test_sign_vault_sig_contains_digest_key(vault_file):
    sig_path = sign_vault(vault_file, SECRET)
    payload = json.loads(sig_path.read_text())
    assert "digest" in payload
    assert "alg" in payload


def test_sign_vault_alg_is_hmac_sha256(vault_file):
    sig_path = sign_vault(vault_file, SECRET)
    payload = json.loads(sig_path.read_text())
    assert payload["alg"] == "hmac-sha256"


# ---------------------------------------------------------------------------
# verify_vault
# ---------------------------------------------------------------------------

def test_verify_vault_passes_for_valid_signature(vault_file):
    sign_vault(vault_file, SECRET)
    # Should not raise
    verify_vault(vault_file, SECRET)


def test_verify_vault_raises_when_no_sig_file(vault_file):
    with pytest.raises(SignatureError, match="not found"):
        verify_vault(vault_file, SECRET)


def test_verify_vault_raises_on_wrong_secret(vault_file):
    sign_vault(vault_file, SECRET)
    with pytest.raises(SignatureError, match="mismatch"):
        verify_vault(vault_file, "wrong-secret")


def test_verify_vault_raises_after_content_tampered(vault_file):
    sign_vault(vault_file, SECRET)
    vault_file.write_bytes(b"tampered-content")
    with pytest.raises(SignatureError, match="mismatch"):
        verify_vault(vault_file, SECRET)


def test_verify_vault_raises_on_malformed_sig_file(vault_file):
    _sig_path(vault_file).write_text("not-json")
    with pytest.raises(SignatureError, match="Malformed"):
        verify_vault(vault_file, SECRET)


# ---------------------------------------------------------------------------
# signature_exists
# ---------------------------------------------------------------------------

def test_signature_exists_false_before_signing(vault_file):
    assert signature_exists(vault_file) is False


def test_signature_exists_true_after_signing(vault_file):
    sign_vault(vault_file, SECRET)
    assert signature_exists(vault_file) is True
