"""Snapshot management: capture and restore .env state at a given vault version."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envault.crypto import decrypt, encrypt
from envault.parser import parse_env, serialise_env
from envault.vault import read_vault, vault_metadata


def _snapshot_dir(vault_path: Path) -> Path:
    """Return the directory where snapshots for *vault_path* are stored."""
    return vault_path.parent / ".envault" / "snapshots"


def _snapshot_path(vault_path: Path, version: int) -> Path:
    return _snapshot_dir(vault_path) / f"v{version}.snap"


def save_snapshot(vault_path: Path, password: str, note: str = "") -> dict[str, Any]:
    """Decrypt the current vault and save an encrypted snapshot for its version.

    Returns a dict with ``version`` and ``fingerprint`` keys.
    """
    raw = read_vault(vault_path, password)
    meta = vault_metadata(vault_path)
    version: int = meta["version"]

    snap_dir = _snapshot_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    payload = json.dumps({"env": raw, "note": note}).encode()
    blob = encrypt(payload, password)

    snap_path = _snapshot_path(vault_path, version)
    snap_path.write_bytes(blob)

    return {"version": version, "path": str(snap_path)}


def load_snapshot(vault_path: Path, version: int, password: str) -> dict[str, str]:
    """Return the env mapping stored in the snapshot for *version*.

    Raises ``FileNotFoundError`` if no snapshot exists for that version.
    Raises ``ValueError`` if the password is wrong or data is corrupt.
    """
    snap_path = _snapshot_path(vault_path, version)
    if not snap_path.exists():
        raise FileNotFoundError(f"No snapshot found for version {version}: {snap_path}")

    blob = snap_path.read_bytes()
    payload = decrypt(blob, password)
    data = json.loads(payload.decode())
    return data["env"]


def list_snapshots(vault_path: Path) -> list[int]:
    """Return a sorted list of version numbers that have saved snapshots."""
    snap_dir = _snapshot_dir(vault_path)
    if not snap_dir.exists():
        return []
    versions = []
    for p in snap_dir.glob("v*.snap"):
        try:
            versions.append(int(p.stem[1:]))
        except ValueError:
            pass
    return sorted(versions)


def restore_snapshot(
    vault_path: Path, version: int, password: str
) -> str:
    """Restore the .env file from a snapshot.  Returns the serialised content."""
    env = load_snapshot(vault_path, version, password)
    content = serialise_env(env)
    env_path = vault_path.parent / ".env"
    env_path.write_text(content)
    return content
