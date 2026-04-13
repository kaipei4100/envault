"""File-system watcher that re-locks a .env file whenever it changes on disk."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional


def _file_hash(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def watch(
    env_path: Path,
    on_change: Callable[[Path], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
    stop_event: Optional[object] = None,
) -> None:
    """Poll *env_path* every *interval* seconds and call *on_change* when it changes.

    Parameters
    ----------
    env_path:
        The plain-text .env file to watch.
    on_change:
        Callback invoked with *env_path* whenever the file content changes.
    interval:
        Polling interval in seconds.
    max_iterations:
        Stop after this many iterations (useful for testing).
    stop_event:
        Any object with a ``is_set()`` method (e.g. ``threading.Event``).
        Watching stops when ``stop_event.is_set()`` returns ``True``.
    """
    if not env_path.exists():
        raise FileNotFoundError(f"watch: path does not exist: {env_path}")

    last_hash = _file_hash(env_path)
    iterations = 0

    while True:
        if stop_event is not None and stop_event.is_set():
            break
        if max_iterations is not None and iterations >= max_iterations:
            break

        time.sleep(interval)
        iterations += 1

        if not env_path.exists():
            continue

        current_hash = _file_hash(env_path)
        if current_hash != last_hash:
            last_hash = current_hash
            on_change(env_path)
