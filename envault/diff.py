"""Human-readable diff output for .env file comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from envault.parser import diff_envs


@dataclass
class DiffLine:
    kind: str  # 'added', 'removed', 'changed', 'unchanged'
    key: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def format(self, show_values: bool = False, mask: bool = True) -> str:
        def _display(v: Optional[str]) -> str:
            if v is None:
                return ""
            if mask:
                return "***"
            return v

        if self.kind == "added":
            val = f" = {_display(self.new_value)}" if show_values else ""
            return f"  + {self.key}{val}"
        elif self.kind == "removed":
            val = f" = {_display(self.old_value)}" if show_values else ""
            return f"  - {self.key}{val}"
        elif self.kind == "changed":
            if show_values:
                return f"  ~ {self.key}: {_display(self.old_value)} -> {_display(self.new_value)}"
            return f"  ~ {self.key}"
        else:
            val = f" = {_display(self.new_value)}" if show_values else ""
            return f"    {self.key}{val}"


def build_diff(
    old: Dict[str, str],
    new: Dict[str, str],
) -> List[DiffLine]:
    """Return a list of DiffLine objects representing changes between two env dicts."""
    raw = diff_envs(old, new)
    lines: List[DiffLine] = []

    added = set(raw.get("added", {}).keys())
    removed = set(raw.get("removed", {}).keys())
    changed_keys = set(raw.get("changed", {}).keys())
    all_keys = sorted(added | removed | changed_keys | set(old.keys()) | set(new.keys()))

    for key in all_keys:
        if key in added:
            lines.append(DiffLine("added", key, new_value=new[key]))
        elif key in removed:
            lines.append(DiffLine("removed", key, old_value=old[key]))
        elif key in changed_keys:
            lines.append(DiffLine("changed", key, old_value=old[key], new_value=new[key]))
        else:
            lines.append(DiffLine("unchanged", key, new_value=new.get(key)))

    return lines


def format_diff(
    old: Dict[str, str],
    new: Dict[str, str],
    show_values: bool = False,
    mask: bool = True,
    skip_unchanged: bool = True,
) -> str:
    """Return a formatted diff string between two env dicts."""
    lines = build_diff(old, new)
    if skip_unchanged:
        lines = [l for l in lines if l.kind != "unchanged"]
    if not lines:
        return "  (no changes)"
    return "\n".join(line.format(show_values=show_values, mask=mask) for line in lines)
