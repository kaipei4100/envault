"""TTL (time-to-live) support for vault secrets.

Allows setting an expiry on individual keys so that envault can warn
or refuse to use stale secrets after a configurable deadline.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_TTL_FILENAME = ".envault_ttl.json"


def _ttl_path(vault_path: str | Path) -> Path:
    """Return the TTL sidecar file path for *vault_path*."""
    return Path(vault_path).parent / _TTL_FILENAME


def _load(vault_path: str | Path) -> dict:
    p = _ttl_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_path: str | Path, data: dict) -> None:
    _ttl_path(vault_path).write_text(json.dumps(data, indent=2))


def set_ttl(vault_path: str | Path, key: str, expires_at: datetime) -> None:
    """Record an expiry timestamp (UTC) for *key* inside *vault_path*."""
    data = _load(vault_path)
    data[key] = expires_at.astimezone(timezone.utc).isoformat()
    _save(vault_path, data)


def get_ttl(vault_path: str | Path, key: str) -> Optional[datetime]:
    """Return the expiry datetime for *key*, or ``None`` if not set."""
    data = _load(vault_path)
    raw = data.get(key)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def delete_ttl(vault_path: str | Path, key: str) -> bool:
    """Remove the TTL for *key*.  Returns ``True`` if a record existed."""
    data = _load(vault_path)
    if key not in data:
        return False
    del data[key]
    _save(vault_path, data)
    return True


def list_ttls(vault_path: str | Path) -> dict[str, datetime]:
    """Return all key → expiry mappings for the vault."""
    return {k: datetime.fromisoformat(v) for k, v in _load(vault_path).items()}


def expired_keys(vault_path: str | Path, *, now: Optional[datetime] = None) -> list[str]:
    """Return keys whose TTL has already passed."""
    if now is None:
        now = datetime.now(timezone.utc)
    return [
        key
        for key, expiry in list_ttls(vault_path).items()
        if expiry <= now
    ]


def expiring_soon(
    vault_path: str | Path,
    within_seconds: int = 86_400,
    *,
    now: Optional[datetime] = None,
) -> list[tuple[str, datetime]]:
    """Return (key, expiry) pairs expiring within *within_seconds* seconds."""
    from datetime import timedelta

    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now + timedelta(seconds=within_seconds)
    return [
        (key, expiry)
        for key, expiry in list_ttls(vault_path).items()
        if now < expiry <= cutoff
    ]
