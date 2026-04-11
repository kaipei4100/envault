"""Key rotation: re-encrypt vault contents under a new password."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.crypto import decrypt, encrypt, fingerprint
from envault.vault import _meta_path, read_vault, write_vault, vault_metadata
from envault.audit import record_event


def rotate_key(
    vault_path: Path,
    old_password: str,
    new_password: str,
    note: Optional[str] = None,
) -> dict:
    """Re-encrypt *vault_path* with *new_password*.

    Steps
    -----
    1. Decrypt the existing vault blob with *old_password*.
    2. Re-encrypt the plaintext with *new_password*.
    3. Overwrite the vault file and bump the version in the meta file.
    4. Record an audit event and return it.

    Raises
    ------
    ValueError
        If *old_password* is wrong or the vault data is corrupted.
    FileNotFoundError
        If *vault_path* does not exist.
    """
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    # 1. Decrypt with the old password (raises on bad password / corruption)
    ciphertext = vault_path.read_bytes()
    plaintext = decrypt(ciphertext, old_password)

    # 2. Re-encrypt with the new password
    new_ciphertext = encrypt(plaintext, new_password)

    # 3. Persist – write_vault handles version bumping and meta update
    write_vault(vault_path, new_ciphertext)

    # 4. Audit
    meta = vault_metadata(vault_path)
    event = record_event(
        vault_dir=vault_path.parent,
        action="rotate",
        version=meta["version"],
        fingerprint=fingerprint(new_password),
        note=note,
    )
    return event


def rotation_needed(vault_path: Path, current_password: str, known_fingerprint: str) -> bool:
    """Return *True* if the vault was encrypted with a different key.

    Compares *known_fingerprint* (the fingerprint the caller trusts) against
    the fingerprint stored in the vault metadata.  A mismatch signals that
    someone else rotated the key and the caller should update their local
    password.
    """
    meta = vault_metadata(vault_path)
    stored = meta.get("fingerprint", "")
    return stored != known_fingerprint
