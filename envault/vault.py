"""Vault module: read, write, and version encrypted .env files."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt, fingerprint

VAULT_EXTENSION = ".vault"
META_EXTENSION = ".vault.meta"


def _meta_path(vault_path: Path) -> Path:
    return vault_path.with_suffix("").with_suffix("").with_name(
        vault_path.name.replace(VAULT_EXTENSION, META_EXTENSION)
    )


def write_vault(
    env_content: str,
    password: str,
    vault_path: Path,
    comment: str = "",
) -> dict:
    """Encrypt *env_content* and write it to *vault_path*.

    Returns the metadata dict that was written alongside the vault file.
    """
    ciphertext = encrypt(env_content.encode(), password)
    vault_path = Path(vault_path)
    vault_path.write_bytes(ciphertext)

    meta = {
        "version": _next_version(vault_path),
        "fingerprint": fingerprint(env_content.encode()),
        "timestamp": int(time.time()),
        "comment": comment,
    }
    meta_path = vault_path.with_suffix("").with_name(
        vault_path.stem + META_EXTENSION
    )
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def read_vault(vault_path: Path, password: str) -> str:
    """Decrypt and return the plaintext content of *vault_path*."""
    vault_path = Path(vault_path)
    ciphertext = vault_path.read_bytes()
    plaintext = decrypt(ciphertext, password)
    return plaintext.decode()


def vault_metadata(vault_path: Path) -> Optional[dict]:
    """Return the metadata dict for *vault_path*, or None if absent."""
    vault_path = Path(vault_path)
    meta_path = vault_path.with_suffix("").with_name(
        vault_path.stem + META_EXTENSION
    )
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text())


def _next_version(vault_path: Path) -> int:
    existing = vault_metadata(vault_path)
    if existing is None:
        return 1
    return existing.get("version", 0) + 1
