"""Export vault contents to various formats (shell, docker, JSON)."""

from __future__ import annotations

import json
import shlex
from typing import Dict, Literal

ExportFormat = Literal["shell", "docker", "json"]


def export_shell(env: Dict[str, str], *, export_keyword: bool = True) -> str:
    """Render env vars as POSIX shell export statements.

    Args:
        env: Mapping of variable names to values.
        export_keyword: Prefix each line with ``export`` when True.

    Returns:
        A newline-terminated string of shell assignments.
    """
    prefix = "export " if export_keyword else ""
    lines = [f"{prefix}{k}={shlex.quote(v)}" for k, v in sorted(env.items())]
    return "\n".join(lines) + "\n" if lines else ""


def export_docker(env: Dict[str, str]) -> str:
    """Render env vars as Docker ``--env`` flags.

    Returns:
        A single string with one ``--env KEY=VALUE`` token-pair per line.
    """
    lines = [f"--env {k}={shlex.quote(v)}" for k, v in sorted(env.items())]
    return "\n".join(lines) + "\n" if lines else ""


def export_json(env: Dict[str, str]) -> str:
    """Render env vars as a pretty-printed JSON object.

    Returns:
        A JSON string with keys sorted alphabetically.
    """
    return json.dumps(dict(sorted(env.items())), indent=2) + "\n"


def export_env(env: Dict[str, str], fmt: ExportFormat) -> str:
    """Dispatch to the appropriate renderer.

    Args:
        env: Mapping of variable names to values.
        fmt: One of ``'shell'``, ``'docker'``, or ``'json'``.

    Returns:
        Formatted string ready to be written to stdout or a file.

    Raises:
        ValueError: If *fmt* is not a recognised format.
    """
    if fmt == "shell":
        return export_shell(env)
    if fmt == "docker":
        return export_docker(env)
    if fmt == "json":
        return export_json(env)
    raise ValueError(f"Unknown export format: {fmt!r}. Choose shell, docker, or json.")
