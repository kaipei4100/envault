"""Search and filter keys across a decrypted vault."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SearchResult:
    key: str
    value: str
    matched_by: str  # 'key', 'value', or 'both'


def search_keys(
    env: Dict[str, str],
    pattern: str,
    *,
    glob: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Return entries whose keys match *pattern*.

    Args:
        env: Parsed environment dictionary.
        pattern: Regex or glob pattern to match against keys.
        glob: Treat *pattern* as a shell glob instead of a regex.
        case_sensitive: Whether matching is case-sensitive.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    results: List[SearchResult] = []

    for key, value in env.items():
        if glob:
            match = fnmatch.fnmatchcase(
                key if case_sensitive else key.upper(),
                pattern if case_sensitive else pattern.upper(),
            )
        else:
            match = bool(re.search(pattern, key, flags))

        if match:
            results.append(SearchResult(key=key, value=value, matched_by="key"))

    return results


def search_values(
    env: Dict[str, str],
    pattern: str,
    *,
    glob: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Return entries whose values match *pattern*."""
    flags = 0 if case_sensitive else re.IGNORECASE
    results: List[SearchResult] = []

    for key, value in env.items():
        if glob:
            match = fnmatch.fnmatchcase(
                value if case_sensitive else value.upper(),
                pattern if case_sensitive else pattern.upper(),
            )
        else:
            match = bool(re.search(pattern, value, flags))

        if match:
            results.append(SearchResult(key=key, value=value, matched_by="value"))

    return results


def search_all(
    env: Dict[str, str],
    pattern: str,
    *,
    glob: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Return entries where key OR value matches *pattern*, deduplicating."""
    flags = 0 if case_sensitive else re.IGNORECASE
    results: List[SearchResult] = []

    for key, value in env.items():
        if glob:
            km = fnmatch.fnmatchcase(
                key if case_sensitive else key.upper(),
                pattern if case_sensitive else pattern.upper(),
            )
            vm = fnmatch.fnmatchcase(
                value if case_sensitive else value.upper(),
                pattern if case_sensitive else pattern.upper(),
            )
        else:
            km = bool(re.search(pattern, key, flags))
            vm = bool(re.search(pattern, value, flags))

        if km and vm:
            results.append(SearchResult(key=key, value=value, matched_by="both"))
        elif km:
            results.append(SearchResult(key=key, value=value, matched_by="key"))
        elif vm:
            results.append(SearchResult(key=key, value=value, matched_by="value"))

    return results


def format_results(results: List[SearchResult], *, show_values: bool = True) -> str:
    """Render search results as a human-readable string."""
    if not results:
        return "No matches found."
    lines = []
    for r in results:
        tag = f"[{r.matched_by}]"
        val_part = f" = {r.value}" if show_values else ""
        lines.append(f"  {tag:<8} {r.key}{val_part}")
    return "\n".join(lines)
