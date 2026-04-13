"""Tests for envault.watch."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from envault.watch import _file_hash, watch


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

def test_file_hash_returns_string(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    assert isinstance(_file_hash(f), str)


def test_file_hash_changes_on_edit(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    h1 = _file_hash(f)
    f.write_text("KEY=changed")
    h2 = _file_hash(f)
    assert h1 != h2


def test_file_hash_stable_for_same_content(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("STABLE=1")
    assert _file_hash(f) == _file_hash(f)


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

def test_watch_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        watch(tmp_path / "missing.env", lambda p: None, max_iterations=0)


def test_watch_calls_on_change_when_file_changes(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("A=1")

    called: list[Path] = []

    def _on_change(path: Path) -> None:
        called.append(path)

    stop = threading.Event()

    def _run() -> None:
        watch(f, _on_change, interval=0.05, stop_event=stop)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    time.sleep(0.1)
    f.write_text("A=2")  # trigger change
    time.sleep(0.2)
    stop.set()
    t.join(timeout=1.0)

    assert len(called) >= 1
    assert called[0] == f


def test_watch_does_not_call_on_change_when_unchanged(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("STABLE=yes")

    called: list[Path] = []
    watch(f, lambda p: called.append(p), interval=0.01, max_iterations=3)

    assert called == []


def test_watch_stops_after_max_iterations(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("X=1")
    # Should return without blocking forever
    watch(f, lambda p: None, interval=0.01, max_iterations=2)


def test_watch_stops_on_stop_event(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("Y=2")
    stop = threading.Event()
    stop.set()  # already set — loop should exit immediately
    watch(f, lambda p: None, interval=0.01, stop_event=stop)
