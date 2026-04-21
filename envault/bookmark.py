"""Bookmark specific vault versions with human-friendly labels."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class BookmarkNotFound(KeyError):
    """Raised when a requested bookmark does not exist."""

    def __str__(self) -> str:  # pragma: no cover
        return f"Bookmark not found: {self.args[0]!r}"


def _bookmark_path(vault_path: str | Path) -> Path:
    p = Path(vault_path)
    return p.with_suffix(".bookmarks.json")


def _load(vault_path: str | Path) -> Dict[str, int]:
    bp = _bookmark_path(vault_path)
    if not bp.exists():
        return {}
    return json.loads(bp.read_text())


def _save(vault_path: str | Path, data: Dict[str, int]) -> None:
    _bookmark_path(vault_path).write_text(json.dumps(data, indent=2))


def set_bookmark(vault_path: str | Path, label: str, version: int) -> dict:
    """Create or overwrite a bookmark pointing to *version*."""
    if not label or not label.strip():
        raise ValueError("Bookmark label must not be empty.")
    if version < 1:
        raise ValueError("Version must be a positive integer.")
    data = _load(vault_path)
    data[label] = version
    _save(vault_path, data)
    return {"label": label, "version": version}


def get_bookmark(vault_path: str | Path, label: str) -> int:
    """Return the version number for *label*, raising BookmarkNotFound if absent."""
    data = _load(vault_path)
    if label not in data:
        raise BookmarkNotFound(label)
    return data[label]


def delete_bookmark(vault_path: str | Path, label: str) -> None:
    """Remove a bookmark by label."""
    data = _load(vault_path)
    if label not in data:
        raise BookmarkNotFound(label)
    del data[label]
    _save(vault_path, data)


def list_bookmarks(vault_path: str | Path) -> List[dict]:
    """Return all bookmarks sorted alphabetically by label."""
    data = _load(vault_path)
    return [
        {"label": lbl, "version": ver}
        for lbl, ver in sorted(data.items())
    ]
