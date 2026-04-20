"""Lock status tracking — records whether a vault is currently locked or unlocked."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional


def _status_path(vault_path: str | Path) -> Path:
    p = Path(vault_path)
    return p.with_suffix(".lockstatus")


def _load(vault_path: str | Path) -> dict:
    path = _status_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(vault_path: str | Path, data: dict) -> None:
    _status_path(vault_path).write_text(json.dumps(data, indent=2))


def set_locked(vault_path: str | Path, identity: str, note: str = "") -> dict:
    """Mark a vault as locked by *identity*."""
    record = {
        "locked": True,
        "identity": identity,
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": note,
    }
    _save(vault_path, record)
    return record


def set_unlocked(vault_path: str | Path) -> dict:
    """Clear the lock on a vault."""
    record = {
        "locked": False,
        "identity": None,
        "locked_at": None,
        "note": "",
    }
    _save(vault_path, record)
    return record


def get_status(vault_path: str | Path) -> dict:
    """Return the current lock status dict (defaults to unlocked if absent)."""
    data = _load(vault_path)
    if not data:
        return {"locked": False, "identity": None, "locked_at": None, "note": ""}
    return data


def is_locked(vault_path: str | Path) -> bool:
    """Return True if the vault is currently locked."""
    return bool(get_status(vault_path).get("locked", False))


def assert_unlocked(vault_path: str | Path) -> None:
    """Raise RuntimeError if the vault is locked."""
    status = get_status(vault_path)
    if status.get("locked"):
        who = status.get("identity", "unknown")
        when = status.get("locked_at", "?")
        raise RuntimeError(f"Vault is locked by '{who}' since {when}")
