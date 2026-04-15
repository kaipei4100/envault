"""Notification hooks for vault events (stdout, webhook, or file log)."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class NotifyResult:
    ok: bool
    channel: str
    message: str
    error: Optional[str] = None


def _notify_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".notify.json")


def load_config(vault_path: Path) -> dict:
    """Load notification config for a vault; returns empty dict if absent."""
    p = _notify_path(vault_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def save_config(vault_path: Path, config: dict) -> None:
    """Persist notification config alongside the vault file."""
    _notify_path(vault_path).write_text(json.dumps(config, indent=2))


def _build_payload(event: str, note: str, version: int) -> dict:
    return {
        "event": event,
        "version": version,
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def notify_webhook(url: str, payload: dict, timeout: int = 5) -> NotifyResult:
    """POST *payload* as JSON to *url*."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return NotifyResult(ok=True, channel="webhook", message=f"HTTP {resp.status}")
    except urllib.error.URLError as exc:
        return NotifyResult(ok=False, channel="webhook", message="", error=str(exc))


def notify_file(log_path: Path, payload: dict) -> NotifyResult:
    """Append *payload* as a JSON line to *log_path*."""
    try:
        with log_path.open("a") as fh:
            fh.write(json.dumps(payload) + "\n")
        return NotifyResult(ok=True, channel="file", message=str(log_path))
    except OSError as exc:
        return NotifyResult(ok=False, channel="file", message="", error=str(exc))


def dispatch(vault_path: Path, event: str, version: int, note: str = "") -> list[NotifyResult]:
    """Read notify config for *vault_path* and dispatch to all configured channels."""
    config = load_config(vault_path)
    if not config:
        return []

    payload = _build_payload(event, note, version)
    results: list[NotifyResult] = []

    if webhook_url := config.get("webhook"):
        results.append(notify_webhook(webhook_url, payload))

    if log_file := config.get("log_file"):
        results.append(notify_file(Path(log_file), payload))

    return results
