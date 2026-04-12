"""Tag management for vault versions — attach, remove, and resolve named tags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_TAGS_FILENAME = ".envault_tags.json"


def _tags_path(vault_dir: Path) -> Path:
    return vault_dir / _TAGS_FILENAME


def _load_tags(vault_dir: Path) -> Dict[str, int]:
    """Return mapping of tag_name -> version number."""
    p = _tags_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_tags(vault_dir: Path, tags: Dict[str, int]) -> None:
    _tags_path(vault_dir).write_text(json.dumps(tags, indent=2))


def set_tag(vault_dir: Path, tag: str, version: int) -> None:
    """Create or update a tag pointing to *version*."""
    if not tag.isidentifier():
        raise ValueError(f"Invalid tag name: {tag!r}. Use letters, digits, and underscores only.")
    tags = _load_tags(vault_dir)
    tags[tag] = version
    _save_tags(vault_dir, tags)


def delete_tag(vault_dir: Path, tag: str) -> None:
    """Remove a tag. Raises KeyError if not found."""
    tags = _load_tags(vault_dir)
    if tag not in tags:
        raise KeyError(f"Tag not found: {tag!r}")
    del tags[tag]
    _save_tags(vault_dir, tags)


def resolve_tag(vault_dir: Path, tag: str) -> int:
    """Return the version number for *tag*. Raises KeyError if not found."""
    tags = _load_tags(vault_dir)
    if tag not in tags:
        raise KeyError(f"Tag not found: {tag!r}")
    return tags[tag]


def list_tags(vault_dir: Path) -> List[Dict[str, object]]:
    """Return a sorted list of {tag, version} dicts."""
    tags = _load_tags(vault_dir)
    return sorted(
        [{"tag": t, "version": v} for t, v in tags.items()],
        key=lambda x: x["tag"],
    )


def find_tags_for_version(vault_dir: Path, version: int) -> List[str]:
    """Return all tag names that point to *version*."""
    tags = _load_tags(vault_dir)
    return sorted(t for t, v in tags.items() if v == version)
