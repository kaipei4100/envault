"""Annotation support — attach freeform notes to specific vault versions."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


class AnnotationNotFound(KeyError):
    def __str__(self) -> str:  # pragma: no cover
        return f"No annotation found for version {self.args[0]}"


def _annotation_path(vault_path: str | Path) -> Path:
    """Return the sibling .annotations.json file for a vault."""
    p = Path(vault_path)
    return p.parent / (p.stem + ".annotations.json")


def _load(vault_path: str | Path) -> dict:
    path = _annotation_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(vault_path: str | Path, data: dict) -> None:
    path = _annotation_path(vault_path)
    path.write_text(json.dumps(data, indent=2))


def set_annotation(
    vault_path: str | Path,
    version: int,
    note: str,
    author: Optional[str] = None,
) -> dict:
    """Attach a note to *version*.  Returns the stored annotation dict."""
    data = _load(vault_path)
    entry = {
        "version": version,
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if author:
        entry["author"] = author
    data[str(version)] = entry
    _save(vault_path, data)
    return entry


def get_annotation(vault_path: str | Path, version: int) -> dict:
    """Return the annotation for *version*, raising AnnotationNotFound if absent."""
    data = _load(vault_path)
    key = str(version)
    if key not in data:
        raise AnnotationNotFound(version)
    return data[key]


def delete_annotation(vault_path: str | Path, version: int) -> bool:
    """Remove the annotation for *version*.  Returns True if it existed."""
    data = _load(vault_path)
    key = str(version)
    if key not in data:
        return False
    del data[key]
    _save(vault_path, data)
    return True


def list_annotations(vault_path: str | Path) -> list[dict]:
    """Return all annotations sorted by version (ascending)."""
    data = _load(vault_path)
    return [data[k] for k in sorted(data, key=lambda x: int(x))]
