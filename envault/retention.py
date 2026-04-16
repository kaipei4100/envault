"""Retention policy: automatically prune old vault versions beyond a configured limit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

_RETENTION_SUFFIX = ".retention.json"


def _retention_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(_RETENTION_SUFFIX)


def _load(vault_path: Path) -> dict:
    p = _retention_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_path: Path, data: dict) -> None:
    _retention_path(vault_path).write_text(json.dumps(data, indent=2))


def set_retention(vault_path: Path, keep: int) -> dict:
    """Persist a retention policy (number of versions to keep) for *vault_path*."""
    if keep < 1:
        raise ValueError("keep must be at least 1")
    data = _load(vault_path)
    data["keep"] = keep
    _save(vault_path, data)
    return dict(data)


def get_retention(vault_path: Path) -> Optional[int]:
    """Return the configured *keep* limit, or None if no policy is set."""
    data = _load(vault_path)
    return data.get("keep")


def delete_retention(vault_path: Path) -> bool:
    """Remove the retention policy file.  Returns True if it existed."""
    p = _retention_path(vault_path)
    if p.exists():
        p.unlink()
        return True
    return False


def apply_retention(vault_path: Path, available_versions: List[int]) -> List[int]:
    """Return the list of version numbers that should be *deleted* to satisfy
    the retention policy.  Versions are sorted ascending; the newest *keep*
    versions are preserved.

    If no policy is configured an empty list is returned (nothing pruned).
    """
    keep = get_retention(vault_path)
    if keep is None:
        return []
    sorted_versions = sorted(available_versions)
    prune_count = max(0, len(sorted_versions) - keep)
    return sorted_versions[:prune_count]


def retention_status(vault_path: Path, available_versions: List[int]) -> dict:
    """Return a summary dict describing the current retention state for *vault_path*.

    Keys:
        ``keep``      – configured limit, or None if no policy is set.
        ``total``     – total number of available versions.
        ``to_prune``  – list of version numbers that would be pruned.
        ``to_keep``   – list of version numbers that would be retained.
    """
    keep = get_retention(vault_path)
    to_prune = apply_retention(vault_path, available_versions)
    to_keep = [v for v in sorted(available_versions) if v not in to_prune]
    return {
        "keep": keep,
        "total": len(available_versions),
        "to_prune": to_prune,
        "to_keep": to_keep,
    }
