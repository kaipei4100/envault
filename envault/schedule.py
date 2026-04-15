"""schedule.py – simple cron-style reminder metadata for vault rotations.

Stores a per-vault schedule (cron expression + optional note) and checks
whether a rotation is overdue based on the last-rotation timestamp recorded
in vault metadata.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SCHEDULE_SUFFIX = ".schedule.json"
_CRON_RE = re.compile(
    r"^(\*|[0-9,\-\*/]+)\s+(\*|[0-9,\-\*/]+)\s+(\*|[0-9,\-\*/]+)"
    r"\s+(\*|[0-9,\-\*/]+)\s+(\*|[0-9,\-\*/]+)$"
)


class InvalidCronExpression(ValueError):
    """Raised when a cron string does not match the expected 5-field format."""


def _schedule_path(vault_path: Path) -> Path:
    return vault_path.with_suffix("").with_suffix(_SCHEDULE_SUFFIX)


def _load(vault_path: Path) -> dict:
    p = _schedule_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_path: Path, data: dict) -> None:
    p = _schedule_path(vault_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def set_schedule(vault_path: Path, cron: str, note: str = "") -> dict:
    """Persist a cron schedule for *vault_path*.

    Parameters
    ----------
    vault_path:
        Path to the encrypted vault file.
    cron:
        A standard 5-field cron expression (minute hour dom month dow).
    note:
        Optional human-readable description.

    Returns the stored schedule record.
    """
    if not _CRON_RE.match(cron.strip()):
        raise InvalidCronExpression(f"Invalid cron expression: {cron!r}")
    record = {
        "cron": cron.strip(),
        "note": note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save(vault_path, record)
    return record


def get_schedule(vault_path: Path) -> Optional[dict]:
    """Return the stored schedule dict, or *None* if none is set."""
    data = _load(vault_path)
    return data if data else None


def delete_schedule(vault_path: Path) -> bool:
    """Remove the schedule file. Returns True if a file was deleted."""
    p = _schedule_path(vault_path)
    if p.exists():
        p.unlink()
        return True
    return False


def rotation_overdue(vault_path: Path, last_rotated_iso: Optional[str]) -> bool:
    """Return True when the schedule exists and the last rotation is overdue.

    Currently supports only ``@daily``, ``@weekly``, and ``@monthly`` aliases
    plus the plain hourly/daily heuristic for numeric expressions (checks the
    *hour* field to determine minimum cadence in hours).
    """
    schedule = get_schedule(vault_path)
    if schedule is None or last_rotated_iso is None:
        return False

    cron = schedule["cron"]
    last = datetime.fromisoformat(last_rotated_iso)
    now = datetime.now(timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    elapsed_hours = (now - last).total_seconds() / 3600

    if cron == "@daily" or cron == "0 0 * * *":
        return elapsed_hours >= 24
    if cron == "@weekly" or cron == "0 0 * * 0":
        return elapsed_hours >= 168
    if cron == "@monthly" or cron == "0 0 1 * *":
        return elapsed_hours >= 720
    # Generic: use hour field to infer cadence
    parts = cron.split()
    hour_field = parts[1]
    if hour_field == "*":
        return elapsed_hours >= 1
    return elapsed_hours >= 24
