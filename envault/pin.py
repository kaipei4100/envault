"""Pin management: lock a vault to a specific version to prevent accidental updates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _pin_path(vault_path: Path) -> Path:
    """Return the .pin sidecar file path for a vault."""
    return vault_path.with_suffix(".pin")


def _load(vault_path: Path) -> dict:
    p = _pin_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(vault_path: Path, data: dict) -> None:
    _pin_path(vault_path).write_text(json.dumps(data, indent=2))


def set_pin(vault_path: Path, version: int, note: str = "") -> None:
    """Pin *vault_path* to *version*."""
    if version < 1:
        raise ValueError(f"Version must be >= 1, got {version}")
    data = {"version": version, "note": note}
    _save(vault_path, data)


def get_pin(vault_path: Path) -> Optional[dict]:
    """Return the pin dict {version, note} or None if no pin is set."""
    data = _load(vault_path)
    return data if data else None


def delete_pin(vault_path: Path) -> bool:
    """Remove the pin file. Returns True if a pin existed, False otherwise."""
    p = _pin_path(vault_path)
    if p.exists():
        p.unlink()
        return True
    return False


class PinViolation(Exception):
    """Raised when an operation would modify a pinned vault."""


def check_pin(vault_path: Path, proposed_version: int) -> None:
    """Raise PinViolation if *proposed_version* conflicts with an active pin."""
    pin = get_pin(vault_path)
    if pin is None:
        return
    pinned = pin["version"]
    if proposed_version != pinned:
        note = f" ({pin['note']})" if pin.get("note") else ""
        raise PinViolation(
            f"Vault is pinned to version {pinned}{note}; "
            f"proposed version {proposed_version} is not allowed."
        )
