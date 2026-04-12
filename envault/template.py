"""Template rendering: substitute .env values into text templates."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


@dataclass
class RenderResult:
    text: str
    substituted: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0


def render_string(template: str, env: Dict[str, str]) -> RenderResult:
    """Replace ``{{ KEY }}`` placeholders with values from *env*.

    Unknown keys are left as-is and recorded in ``RenderResult.missing``.
    """
    substituted: List[str] = []
    missing: List[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in env:
            substituted.append(key)
            return env[key]
        missing.append(key)
        return match.group(0)

    rendered = _PLACEHOLDER_RE.sub(_replace, template)
    return RenderResult(text=rendered, substituted=substituted, missing=missing)


def render_file(
    template_path: Path,
    env: Dict[str, str],
    output_path: Optional[Path] = None,
) -> RenderResult:
    """Render a template file and optionally write the result.

    If *output_path* is ``None`` the rendered text is only returned.
    """
    template_text = template_path.read_text(encoding="utf-8")
    result = render_string(template_text, env)
    if output_path is not None:
        output_path.write_text(result.text, encoding="utf-8")
    return result


def list_placeholders(template: str) -> List[str]:
    """Return a deduplicated, ordered list of placeholder keys in *template*."""
    seen: dict[str, None] = {}
    for match in _PLACEHOLDER_RE.finditer(template):
        seen[match.group(1)] = None
    return list(seen)
