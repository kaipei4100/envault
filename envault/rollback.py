"""rollback.py — Restore a vault to a previous snapshot version."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envault.snapshot import list_snapshots, load_snapshot, save_snapshot
from envault.vault import vault_metadata, write_vault
from envault.audit import record_event


class RollbackError(Exception):
    """Raised when a rollback cannot be completed."""


@dataclass
class RollbackResult:
    vault_path: Path
    from_version: int
    to_version: int
    new_version: int
    keys_restored: int
    audit: dict = field(default_factory=dict)


def rollback(
    vault_path: Path,
    password: str,
    target_version: int,
    note: Optional[str] = None,
) -> RollbackResult:
    """Roll back *vault_path* to *target_version*.

    The rollback is non-destructive: the current state is preserved in the
    audit log and the restored content is written as a *new* vault version.

    Raises
    ------
    RollbackError
        If *target_version* does not exist in the snapshot history.
    """
    available = {s["version"]: s for s in list_snapshots(vault_path)}
    if target_version not in available:
        raise RollbackError(
            f"Version {target_version} not found. "
            f"Available: {sorted(available)}"
        )

    meta = vault_metadata(vault_path)
    from_version = meta["version"]

    env = load_snapshot(vault_path, password, target_version)

    new_version = write_vault(vault_path, password, env)
    save_snapshot(vault_path, password, env)

    audit = record_event(
        vault_path,
        event="rollback",
        note=note or f"rolled back from v{from_version} to v{target_version}",
        extra={
            "from_version": from_version,
            "to_version": target_version,
            "new_version": new_version,
        },
    )

    return RollbackResult(
        vault_path=vault_path,
        from_version=from_version,
        to_version=target_version,
        new_version=new_version,
        keys_restored=len(env),
        audit=audit,
    )


def can_rollback(vault_path: Path) -> bool:
    """Return True if there is at least one snapshot to roll back to."""
    snapshots = list_snapshots(vault_path)
    return len(snapshots) >= 2
