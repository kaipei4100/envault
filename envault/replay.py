"""Replay: restore a vault to a specific historical version from audit log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.audit import read_events
from envault.snapshot import load_snapshot, list_snapshots
from envault.vault import write_vault, vault_metadata


class ReplayError(Exception):
    """Raised when a replay operation cannot be completed."""


def list_replayable(vault_path: Path) -> list[dict]:
    """Return audit events that correspond to available snapshots.

    Each entry contains the version, timestamp, action, and optional note.
    """
    events = read_events(vault_path)
    available = {s["version"] for s in list_snapshots(vault_path)}
    return [
        e for e in events
        if e.get("version") in available
    ]


def replay_to_version(
    vault_path: Path,
    target_version: int,
    password: str,
    note: Optional[str] = None,
) -> dict:
    """Restore vault contents to *target_version* by replaying its snapshot.

    The current vault is overwritten with the decrypted snapshot data, and a
    new vault version is written so the history is preserved.

    Returns an audit-style dict describing the replay event.
    """
    snapshots = {s["version"]: s for s in list_snapshots(vault_path)}
    if target_version not in snapshots:
        raise ReplayError(
            f"No snapshot found for version {target_version}. "
            f"Available: {sorted(snapshots)}"
        )

    # Decrypt the historical snapshot
    env_vars = load_snapshot(vault_path, target_version, password)

    # Re-encrypt under the same password into a new vault version
    meta = vault_metadata(vault_path)
    current_version = meta.get("version", 0)
    new_version = current_version + 1

    write_vault(vault_path, env_vars, password)

    event: dict = {
        "action": "replay",
        "version": new_version,
        "replayed_from": target_version,
    }
    if note:
        event["note"] = note
    return event
