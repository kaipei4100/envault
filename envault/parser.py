"""Parse and serialise .env file content."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

_LINE_RE = re.compile(
    r"^\s*(?:export\s+)?"  # optional 'export'
    r"([A-Za-z_][A-Za-z0-9_]*)"  # key
    r"\s*=\s*"             # equals
    r"([\s\S]*?)"          # value (lazy)
    r"\s*$"
)


def parse_env(text: str) -> Dict[str, str]:
    """Parse *.env* text and return a dict of key/value pairs.

    Lines starting with ``#`` and blank lines are ignored.
    Quoted values (single or double) are unquoted.
    """
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _LINE_RE.match(stripped)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        value = _unquote(value)
        result[key] = value
    return result


def serialise_env(pairs: Dict[str, str]) -> str:
    """Serialise a dict of key/value pairs to *.env* text."""
    lines: List[str] = []
    for key, value in pairs.items():
        if _needs_quoting(value):
            value = '"' + value.replace('"', '\\"') + '"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def diff_envs(
    old: Dict[str, str], new: Dict[str, str]
) -> Tuple[Dict[str, str], List[str], Dict[str, Tuple[str, str]]]:
    """Return *(added, removed, changed)* between two env dicts."""
    added = {k: v for k, v in new.items() if k not in old}
    removed = [k for k in old if k not in new]
    changed = {
        k: (old[k], new[k])
        for k in old
        if k in new and old[k] != new[k]
    }
    return added, removed, changed


def _unquote(value: str) -> str:
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            return value[1:-1].replace(f"\\{quote}", quote)
    return value


def _needs_quoting(value: str) -> bool:
    return bool(re.search(r"[\s#\"']", value))
