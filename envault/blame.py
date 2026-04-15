"""blame.py – trace which audit event last changed each key in a vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.audit import read_events
from envault.crypto import decrypt
from envault.parser import parse_env
from envault.vault import read_vault


@dataclass
class BlameLine:
    key: str
    value: str
    version: int
    event: str
    user: Optional[str] = None
    note: Optional[str] = None
    timestamp: Optional[str] = None


def blame(vault_path: Path, password: str) -> List[BlameLine]:
    """Return a BlameLine for every key showing which version last touched it."""
    events = read_events(vault_path)
    # Walk events oldest-first so later events overwrite earlier ones.
    events_sorted = sorted(events, key=lambda e: e.get("version", 0))

    # Map key -> BlameLine from the most-recent event that introduced/changed it.
    blame_map: Dict[str, BlameLine] = {}
    prev_env: Dict[str, str] = {}

    for event in events_sorted:
        ver = event.get("version")
        if ver is None:
            continue
        try:
            raw = read_vault(vault_path, ver)
            current_env = parse_env(decrypt(raw, password).decode())
        except Exception:
            continue

        for key, value in current_env.items():
            if key not in prev_env or prev_env[key] != value:
                blame_map[key] = BlameLine(
                    key=key,
                    value=value,
                    version=ver,
                    event=event.get("event", "unknown"),
                    user=event.get("user"),
                    note=event.get("note"),
                    timestamp=event.get("timestamp"),
                )
        # Keys removed in this version keep their last-seen BlameLine.
        prev_env = current_env

    return sorted(blame_map.values(), key=lambda b: b.key)


def format_blame(lines: List[BlameLine], show_values: bool = False) -> str:
    """Render blame output as a human-readable string."""
    if not lines:
        return "(no keys found)"
    rows = []
    for bl in lines:
        who = bl.user or "unknown"
        note = f"  # {bl.note}" if bl.note else ""
        val_part = f" = {bl.value!r}" if show_values else ""
        rows.append(
            f"v{bl.version:<4} {bl.timestamp or '?':<26} {who:<20} {bl.key}{val_part}{note}"
        )
    header = f"{'ver':<5} {'timestamp':<26} {'user':<20} key"
    separator = "-" * max(len(header), max(len(r) for r in rows))
    return "\n".join([header, separator] + rows)
