"""Rotation reminders: warn when a vault secret is older than a threshold."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SUFFIX = ".remind.json"


def _remind_path(vault_path: str | Path) -> Path:
    return Path(vault_path).with_suffix(_SUFFIX)


def _load(vault_path: str | Path) -> dict:
    p = _remind_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_path: str | Path, data: dict) -> None:
    _remind_path(vault_path).write_text(json.dumps(data, indent=2))


def set_reminder(vault_path: str | Path, max_age_days: int) -> dict:
    """Store a rotation-reminder policy (max age in days)."""
    if max_age_days < 1:
        raise ValueError("max_age_days must be >= 1")
    data = _load(vault_path)
    data["max_age_days"] = max_age_days
    _save(vault_path, data)
    return {"max_age_days": max_age_days}


def get_reminder(vault_path: str | Path) -> Optional[int]:
    """Return configured max_age_days or None."""
    return _load(vault_path).get("max_age_days")


def delete_reminder(vault_path: str | Path) -> None:
    p = _remind_path(vault_path)
    if p.exists():
        p.unlink()


def check_reminder(vault_path: str | Path, last_rotated_iso: str) -> dict:
    """Return a dict with 'due' (bool) and 'age_days' (int).

    Parameters
    ----------
    vault_path:        path to the vault file
    last_rotated_iso:  ISO-8601 timestamp of the last key rotation
    """
    max_age = get_reminder(vault_path)
    rotated_at = datetime.fromisoformat(last_rotated_iso)
    if rotated_at.tzinfo is None:
        rotated_at = rotated_at.replace(tzinfo=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    age_days = (now - rotated_at).days
    due = max_age is not None and age_days >= max_age
    return {"due": due, "age_days": age_days, "max_age_days": max_age}
