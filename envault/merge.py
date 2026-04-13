"""Merge two decrypted env dicts with configurable conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ConflictStrategy(str, Enum):
    OURS = "ours"       # keep value from base
    THEIRS = "theirs"   # take value from incoming
    ERROR = "error"     # raise on any conflict


@dataclass
class MergeConflict:
    key: str
    base_value: str
    incoming_value: str

    def __str__(self) -> str:
        return (
            f"  {self.key}: '{self.base_value}' (base) "
            f"vs '{self.incoming_value}' (incoming)"
        )


@dataclass
class MergeResult:
    env: Dict[str, str]
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    conflicts: List[MergeConflict] = field(default_factory=list)
    strategy_used: ConflictStrategy = ConflictStrategy.OURS

    @property
    def ok(self) -> bool:
        return len(self.conflicts) == 0 or self.strategy_used != ConflictStrategy.ERROR


class MergeConflictError(Exception):
    def __init__(self, conflicts: List[MergeConflict]) -> None:
        self.conflicts = conflicts
        lines = ["Merge conflicts detected:"] + [str(c) for c in conflicts]
        super().__init__("\n".join(lines))


def merge_envs(
    base: Dict[str, str],
    incoming: Dict[str, str],
    strategy: ConflictStrategy = ConflictStrategy.OURS,
    exclude_keys: Optional[List[str]] = None,
) -> MergeResult:
    """Merge *incoming* into *base*, returning a MergeResult.

    Keys present only in *incoming* are always added.
    Keys present only in *base* are kept unchanged.
    Conflicting keys (different values) are resolved by *strategy*.
    """
    exclude = set(exclude_keys or [])
    result: Dict[str, str] = dict(base)
    added: List[str] = []
    updated: List[str] = []
    conflicts: List[MergeConflict] = []

    for key, inc_val in incoming.items():
        if key in exclude:
            continue
        if key not in base:
            result[key] = inc_val
            added.append(key)
        elif base[key] != inc_val:
            conflict = MergeConflict(key, base[key], inc_val)
            conflicts.append(conflict)
            if strategy == ConflictStrategy.ERROR:
                pass  # collect all, raise below
            elif strategy == ConflictStrategy.THEIRS:
                result[key] = inc_val
                updated.append(key)
            # OURS: keep base value — no change needed

    if conflicts and strategy == ConflictStrategy.ERROR:
        raise MergeConflictError(conflicts)

    removed = [k for k in base if k not in incoming and k not in exclude]

    return MergeResult(
        env=result,
        added=added,
        removed=removed,
        updated=updated,
        conflicts=conflicts,
        strategy_used=strategy,
    )
