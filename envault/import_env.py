"""Import utilities: read an existing .env file and lock it into a vault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envault.parser import parse_env, serialise_env
from envault.vault import write_vault, vault_metadata
from envault.audit import record_event


def import_env_file(
    env_path: str | Path,
    vault_dir: str | Path,
    password: str,
    note: Optional[str] = None,
) -> dict:
    """Read a plain-text .env file and write it as an encrypted vault.

    Parameters
    ----------
    env_path:  Path to the source .env file.
    vault_dir: Directory where the vault (and metadata) will be stored.
    password:  Encryption password.
    note:      Optional human-readable note stored in the audit log.

    Returns
    -------
    An audit-event dict describing the import.
    """
    env_path = Path(env_path)
    vault_dir = Path(vault_dir)

    if not env_path.exists():
        raise FileNotFoundError(f"Source .env file not found: {env_path}")

    raw_text = env_path.read_text(encoding="utf-8")
    pairs = parse_env(raw_text)

    if not pairs:
        raise ValueError(f"No valid key=value pairs found in {env_path}")

    canonical = serialise_env(pairs)
    version = write_vault(vault_dir, canonical.encode(), password)

    event = record_event(
        vault_dir=vault_dir,
        action="import",
        version=version,
        note=note or f"Imported from {env_path.name}",
    )
    return event


def preview_import(env_path: str | Path) -> dict[str, str]:
    """Parse a .env file and return the key/value pairs without writing anything.

    Useful for a dry-run or confirmation prompt in the CLI.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        raise FileNotFoundError(f"Source .env file not found: {env_path}")

    raw_text = env_path.read_text(encoding="utf-8")
    return parse_env(raw_text)
