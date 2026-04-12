"""Pre/post hook support for envault vault operations."""

from __future__ import annotations

import subprocess
import os
from pathlib import Path
from typing import Optional

HOOKS_FILE = ".envault-hooks"

_VALID_EVENTS = {
    "pre-lock",
    "post-lock",
    "pre-unlock",
    "post-unlock",
    "pre-push",
    "post-push",
    "post-pull",
}


def _hooks_path(vault_dir: Path) -> Path:
    return vault_dir / HOOKS_FILE


def load_hooks(vault_dir: Path) -> dict[str, str]:
    """Load hooks from .envault-hooks (INI-style: event=command)."""
    path = _hooks_path(vault_dir)
    if not path.exists():
        return {}
    hooks: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        event, _, command = line.partition("=")
        event = event.strip()
        command = command.strip()
        if event in _VALID_EVENTS and command:
            hooks[event] = command
    return hooks


def save_hooks(vault_dir: Path, hooks: dict[str, str]) -> None:
    """Persist hooks to .envault-hooks."""
    for event in hooks:
        if event not in _VALID_EVENTS:
            raise ValueError(f"Unknown hook event: {event!r}")
    path = _hooks_path(vault_dir)
    lines = ["# envault hooks — event=shell command\n"]
    for event, command in sorted(hooks.items()):
        lines.append(f"{event}={command}\n")
    path.write_text("".join(lines))


def run_hook(
    vault_dir: Path,
    event: str,
    env: Optional[dict[str, str]] = None,
) -> Optional[int]:
    """Run the hook for *event* if one is defined. Returns exit code or None."""
    hooks = load_hooks(vault_dir)
    command = hooks.get(event)
    if not command:
        return None
    merged_env = {**os.environ, **(env or {})}
    result = subprocess.run(command, shell=True, env=merged_env)
    return result.returncode
