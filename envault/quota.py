"""Vault storage quota tracking and enforcement."""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


_QUOTA_FILENAME = ".quota.json"


@dataclass
class QuotaExceeded(Exception):
    used: int
    limit: int

    def __str__(self) -> str:
        return (
            f"Quota exceeded: {self.used} bytes used, limit is {self.limit} bytes"
        )


def _quota_path(vault_path: Path) -> Path:
    return vault_path.parent / _QUOTA_FILENAME


def _load(vault_path: Path) -> dict:
    p = _quota_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_path: Path, data: dict) -> None:
    _quota_path(vault_path).write_text(json.dumps(data, indent=2))


def set_quota(vault_path: Path, max_bytes: int) -> dict:
    """Set a byte-size quota for the vault directory."""
    data = _load(vault_path)
    data["max_bytes"] = max_bytes
    _save(vault_path, data)
    return dict(data)


def get_quota(vault_path: Path) -> Optional[int]:
    """Return the configured quota in bytes, or None if unset."""
    return _load(vault_path).get("max_bytes")


def delete_quota(vault_path: Path) -> bool:
    """Remove the quota setting. Returns True if it existed."""
    data = _load(vault_path)
    if "max_bytes" not in data:
        return False
    del data["max_bytes"]
    _save(vault_path, data)
    return True


def current_usage(vault_path: Path) -> int:
    """Return total bytes used by all vault files in the same directory."""
    return sum(
        f.stat().st_size
        for f in vault_path.parent.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )


def check_quota(vault_path: Path) -> dict:
    """Check current usage against quota. Raises QuotaExceeded if over limit."""
    used = current_usage(vault_path)
    limit = get_quota(vault_path)
    result = {"used_bytes": used, "limit_bytes": limit, "exceeded": False}
    if limit is not None and used > limit:
        result["exceeded"] = True
        raise QuotaExceeded(used=used, limit=limit)
    return result
