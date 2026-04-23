"""Prune old vault snapshots beyond a configurable keep count."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.snapshot import _snapshot_dir, _snapshot_path, list_snapshots


@dataclass
class PruneResult:
    kept: List[int] = field(default_factory=list)
    removed: List[int] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        return (
            f"Kept {len(self.kept)} snapshot(s), "
            f"removed {len(self.removed)} snapshot(s)."
        )


def _prune_config_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".prune.json")


def set_prune_policy(vault_path: Path, keep: int) -> dict:
    """Persist a keep-N prune policy for *vault_path*."""
    if keep < 1:
        raise ValueError("keep must be >= 1")
    cfg = {"keep": keep}
    _prune_config_path(vault_path).write_text(json.dumps(cfg))
    return cfg


def get_prune_policy(vault_path: Path) -> dict | None:
    """Return the prune policy dict, or None if not configured."""
    p = _prune_config_path(vault_path)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def prune(vault_path: Path, keep: int) -> PruneResult:
    """Delete snapshots older than the *keep* most-recent versions.

    Snapshots are identified by the files produced by
    :func:`envault.snapshot.save_snapshot`.  The *keep* highest version
    numbers are retained; everything else is deleted.
    """
    if keep < 1:
        raise ValueError("keep must be >= 1")

    entries = list_snapshots(vault_path)          # [{version, path}, ...]
    versions = sorted(e["version"] for e in entries)

    to_keep = set(versions[-keep:])
    to_remove = [v for v in versions if v not in to_keep]

    for version in to_remove:
        snap = _snapshot_path(vault_path, version)
        if snap.exists():
            snap.unlink()

    return PruneResult(kept=sorted(to_keep), removed=to_remove)
