"""Audit log support for envault — records vault operations with timestamps."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILENAME = ".envault_audit.jsonl"


def _audit_path(vault_dir: str | Path) -> Path:
    """Return the path to the audit log file for a given vault directory."""
    return Path(vault_dir) / AUDIT_FILENAME


def record_event(
    vault_dir: str | Path,
    action: str,
    version: int,
    user: Optional[str] = None,
    note: Optional[str] = None,
) -> dict:
    """Append a single audit event to the JSONL audit log.

    Parameters
    ----------
    vault_dir: directory that contains the vault files.
    action:    short verb, e.g. 'lock', 'unlock', 'push', 'pull'.
    version:   vault version this event relates to.
    user:      optional identifier for the actor (defaults to OS login name).
    note:      optional free-text annotation.

    Returns the event dict that was written.
    """
    if user is None:
        try:
            user = os.getlogin()
        except OSError:
            user = os.environ.get("USER", "unknown")

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "version": version,
        "user": user,
    }
    if note:
        event["note"] = note

    log_path = _audit_path(vault_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")

    return event


def read_events(vault_dir: str | Path) -> List[dict]:
    """Return all audit events from the log, oldest first."""
    log_path = _audit_path(vault_dir)
    if not log_path.exists():
        return []
    events: List[dict] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def format_events(events: List[dict]) -> str:
    """Return a human-readable table of audit events."""
    if not events:
        return "No audit events recorded."
    lines = [f"{'Timestamp':<32} {'Action':<10} {'Ver':>4}  {'User':<20} Note"]
    lines.append("-" * 80)
    for ev in events:
        lines.append(
            f"{ev['timestamp']:<32} {ev['action']:<10} {ev['version']:>4}  "
            f"{ev.get('user', ''):<20} {ev.get('note', '')}"
        )
    return "\n".join(lines)
