"""Key aliasing — map short names to full environment variable keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _alias_path(vault_path: str | Path) -> Path:
    p = Path(vault_path)
    return p.with_suffix(".aliases.json")


def _load(vault_path: str | Path) -> Dict[str, str]:
    ap = _alias_path(vault_path)
    if not ap.exists():
        return {}
    return json.loads(ap.read_text())


def _save(vault_path: str | Path, data: Dict[str, str]) -> None:
    _alias_path(vault_path).write_text(json.dumps(data, indent=2))


def set_alias(vault_path: str | Path, alias: str, key: str) -> Dict[str, str]:
    """Map *alias* -> *key* and persist."""
    if not alias or not key:
        raise ValueError("alias and key must be non-empty strings")
    data = _load(vault_path)
    data[alias] = key
    _save(vault_path, data)
    return {"alias": alias, "key": key}


def get_alias(vault_path: str | Path, alias: str) -> Optional[str]:
    """Return the key mapped to *alias*, or None if not set."""
    return _load(vault_path).get(alias)


def delete_alias(vault_path: str | Path, alias: str) -> bool:
    """Remove *alias*. Returns True if it existed."""
    data = _load(vault_path)
    if alias not in data:
        return False
    del data[alias]
    _save(vault_path, data)
    return True


def list_aliases(vault_path: str | Path) -> Dict[str, str]:
    """Return all alias -> key mappings."""
    return dict(sorted(_load(vault_path).items()))


def resolve(vault_path: str | Path, alias_or_key: str) -> str:
    """Return the real key for *alias_or_key*, falling back to the value itself."""
    return _load(vault_path).get(alias_or_key, alias_or_key)
