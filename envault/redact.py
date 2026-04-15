"""Redaction helpers — mask sensitive values before display or logging."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should always be fully redacted.
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)"),
]

# Partial-reveal config: show first N and last M chars, mask the middle.
_PARTIAL_REVEAL_MIN_LEN = 8
_MASK_CHAR = "*"


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.redacted_keys) > 0


def is_sensitive(key: str) -> bool:
    """Return True if *key* matches any sensitive pattern."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def mask_value(value: str, partial: bool = False) -> str:
    """Return a masked version of *value*.

    When *partial* is True and the value is long enough, reveal the first
    two and last two characters and mask the rest.
    """
    if not value:
        return value
    if partial and len(value) >= _PARTIAL_REVEAL_MIN_LEN:
        return value[:2] + _MASK_CHAR * (len(value) - 4) + value[-2:]
    return _MASK_CHAR * len(value)


def redact_env(
    env: Dict[str, str],
    extra_keys: Optional[List[str]] = None,
    partial: bool = False,
) -> RedactResult:
    """Return a :class:`RedactResult` with sensitive values masked.

    Parameters
    ----------
    env:
        The environment mapping to redact.
    extra_keys:
        Additional key names (exact, case-insensitive) to treat as sensitive.
    partial:
        When True, use partial masking instead of full masking.
    """
    extra = {k.upper() for k in (extra_keys or [])}
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        if is_sensitive(key) or key.upper() in extra:
            redacted[key] = mask_value(value, partial=partial)
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(original=env, redacted=redacted, redacted_keys=sorted(redacted_keys))
