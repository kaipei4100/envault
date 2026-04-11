"""Profile management for envault — named configurations for backend, bucket, and encryption settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_PROFILE = "default"
_CONFIG_DIR = Path.home() / ".envault"
_CONFIG_FILE = _CONFIG_DIR / "profiles.json"


def _load_all() -> dict[str, Any]:
    """Load all profiles from the config file, returning an empty dict if absent."""
    if not _CONFIG_FILE.exists():
        return {}
    with _CONFIG_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_all(profiles: dict[str, Any]) -> None:
    """Persist all profiles to disk, creating the config directory if needed."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(profiles, fh, indent=2)
        fh.write("\n")


def save_profile(name: str, config: dict[str, Any]) -> None:
    """Create or overwrite a named profile."""
    profiles = _load_all()
    profiles[name] = config
    _save_all(profiles)


def load_profile(name: str = _DEFAULT_PROFILE) -> dict[str, Any]:
    """Return the config dict for *name*, raising KeyError if it does not exist."""
    profiles = _load_all()
    if name not in profiles:
        raise KeyError(f"Profile '{name}' not found. Run 'envault profile set' to create it.")
    return profiles[name]


def delete_profile(name: str) -> bool:
    """Remove a profile by name.  Returns True if it existed, False otherwise."""
    profiles = _load_all()
    if name not in profiles:
        return False
    del profiles[name]
    _save_all(profiles)
    return True


def list_profiles() -> list[str]:
    """Return a sorted list of all profile names."""
    return sorted(_load_all().keys())


def profile_exists(name: str) -> bool:
    return name in _load_all()
