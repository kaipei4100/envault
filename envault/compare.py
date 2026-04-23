"""compare.py – compare two vault versions side-by-side."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.snapshot import load_snapshot
from envault.diff import build_diff, DiffLine


@dataclass
class CompareResult:
    vault_path: str
    version_a: int
    version_b: int
    diff: List[DiffLine] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(line.kind == "unchanged" for line in self.diff)

    @property
    def added(self) -> List[DiffLine]:
        return [d for d in self.diff if d.kind == "added"]

    @property
    def removed(self) -> List[DiffLine]:
        return [d for d in self.diff if d.kind == "removed"]

    @property
    def changed(self) -> List[DiffLine]:
        return [d for d in self.diff if d.kind == "changed"]


def compare_versions(
    vault_path: str,
    password: str,
    version_a: int,
    version_b: int,
) -> CompareResult:
    """Load two snapshots and return a CompareResult with their diff."""
    env_a = load_snapshot(vault_path, password, version_a)
    env_b = load_snapshot(vault_path, password, version_b)
    diff = build_diff(env_a, env_b)
    return CompareResult(
        vault_path=vault_path,
        version_a=version_a,
        version_b=version_b,
        diff=diff,
    )


def format_compare(result: CompareResult, *, show_unchanged: bool = False) -> str:
    """Render a CompareResult as a human-readable string."""
    lines: List[str] = [
        f"Comparing v{result.version_a} → v{result.version_b}  ({result.vault_path})",
        "-" * 60,
    ]
    for d in result.diff:
        if d.kind == "unchanged" and not show_unchanged:
            continue
        if d.kind == "added":
            lines.append(f"  + {d.key}={d.new_value}")
        elif d.kind == "removed":
            lines.append(f"  - {d.key}={d.old_value}")
        elif d.kind == "changed":
            lines.append(f"  ~ {d.key}: {d.old_value!r} → {d.new_value!r}")
        else:
            lines.append(f"    {d.key}={d.new_value}")
    if result.ok:
        lines.append("(no differences)")
    return "\n".join(lines)
