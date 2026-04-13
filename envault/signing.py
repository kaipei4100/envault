"""Vault signing — attach and verify HMAC signatures on vault files."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

_SIG_SUFFIX = ".sig"


def _sig_path(vault_path: Path) -> Path:
    """Return the companion signature file path for *vault_path*."""
    return vault_path.with_suffix(vault_path.suffix + _SIG_SUFFIX)


def _compute_hmac(data: bytes, secret: str) -> str:
    """Return a hex-encoded HMAC-SHA256 digest of *data* using *secret*."""
    key = secret.encode()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def sign_vault(vault_path: Path, secret: str) -> Path:
    """Compute an HMAC signature for *vault_path* and write it to a .sig file.

    Returns the path of the written signature file.
    """
    data = vault_path.read_bytes()
    digest = _compute_hmac(data, secret)
    sig_path = _sig_path(vault_path)
    payload = json.dumps({"alg": "hmac-sha256", "digest": digest}, indent=2)
    sig_path.write_text(payload)
    return sig_path


class SignatureError(Exception):
    """Raised when a vault signature is missing or invalid."""


def verify_vault(vault_path: Path, secret: str) -> None:
    """Verify the HMAC signature of *vault_path*.

    Raises:
        SignatureError: if the signature file is absent or the digest does not
            match the vault content.
    """
    sig_path = _sig_path(vault_path)
    if not sig_path.exists():
        raise SignatureError(f"Signature file not found: {sig_path}")

    try:
        payload = json.loads(sig_path.read_text())
        stored_digest: str = payload["digest"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise SignatureError(f"Malformed signature file: {exc}") from exc

    data = vault_path.read_bytes()
    expected = _compute_hmac(data, secret)

    if not hmac.compare_digest(expected, stored_digest):
        raise SignatureError(
            "Vault signature mismatch — file may have been tampered with."
        )


def signature_exists(vault_path: Path) -> bool:
    """Return True if a signature file exists for *vault_path*."""
    return _sig_path(vault_path).exists()
