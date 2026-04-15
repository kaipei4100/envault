"""Access control: per-key read/write permission rules stored alongside the vault."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

# Permission levels (ordered by privilege)
READ = "read"
WRITE = "write"
ADMIN = "admin"

LEVELS = [READ, WRITE, ADMIN]


def _access_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault_access.json"


def _load(vault_dir: Path) -> Dict:
    p = _access_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_dir: Path, data: Dict) -> None:
    _access_path(vault_dir).write_text(json.dumps(data, indent=2))


def set_permission(vault_dir: Path, identity: str, level: str) -> None:
    """Grant *identity* the given permission *level*."""
    if level not in LEVELS:
        raise ValueError(f"Unknown permission level '{level}'. Choose from: {LEVELS}")
    data = _load(vault_dir)
    data[identity] = level
    _save(vault_dir, data)


def get_permission(vault_dir: Path, identity: str) -> Optional[str]:
    """Return the permission level for *identity*, or None if not set."""
    return _load(vault_dir).get(identity)


def revoke_permission(vault_dir: Path, identity: str) -> None:
    """Remove *identity* from the access list."""
    data = _load(vault_dir)
    if identity not in data:
        raise KeyError(f"Identity '{identity}' not found in access list")
    del data[identity]
    _save(vault_dir, data)


def list_permissions(vault_dir: Path) -> List[Dict]:
    """Return all identities and their levels, sorted by identity name."""
    data = _load(vault_dir)
    return [{"identity": k, "level": v} for k, v in sorted(data.items())]


def check_permission(vault_dir: Path, identity: str, required: str) -> None:
    """Raise PermissionError if *identity* does not have at least *required* level."""
    if required not in LEVELS:
        raise ValueError(f"Unknown required level '{required}'")
    level = get_permission(vault_dir, identity)
    if level is None:
        raise PermissionError(f"Identity '{identity}' has no access permissions")
    if LEVELS.index(level) < LEVELS.index(required):
        raise PermissionError(
            f"Identity '{identity}' has '{level}' but '{required}' is required"
        )


def has_permission(vault_dir: Path, identity: str, required: str) -> bool:
    """Return True if *identity* has at least *required* level, False otherwise.

    Unlike :func:`check_permission`, this never raises; it is intended for
    conditional logic where a boolean result is more convenient than catching
    a ``PermissionError``.
    """
    if required not in LEVELS:
        raise ValueError(f"Unknown required level '{required}'")
    level = get_permission(vault_dir, identity)
    if level is None:
        return False
    return LEVELS.index(level) >= LEVELS.index(required)
