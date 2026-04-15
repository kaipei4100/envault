"""Tests for envault.notify."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault import notify


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


# --- config persistence ---

def test_notify_path_has_correct_suffix(vault_file):
    p = notify._notify_path(vault_file)
    assert p.name == "secrets.notify.json"


def test_load_config_missing_returns_empty(vault_file):
    assert notify.load_config(vault_file) == {}


def test_save_and_load_config_roundtrip(vault_file):
    cfg = {"webhook": "https://example.com/hook", "log_file": "/tmp/out.log"}
    notify.save_config(vault_file, cfg)
    loaded = notify.load_config(vault_file)
    assert loaded == cfg


def test_save_config_creates_file(vault_file):
    notify.save_config(vault_file, {"webhook": "https://x.io"})
    assert notify._notify_path(vault_file).exists()


# --- payload builder ---

def test_build_payload_contains_expected_keys():
    payload = notify._build_payload("lock", "routine", 3)
    assert payload["event"] == "lock"
    assert payload["version"] == 3
    assert payload["note"] == "routine"
    assert "timestamp" in payload


# --- webhook ---

def test_notify_webhook_returns_ok_on_success():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = notify.notify_webhook("https://example.com", {"event": "lock"})

    assert result.ok is True
    assert result.channel == "webhook"
    assert "200" in result.message


def test_notify_webhook_returns_error_on_failure():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        result = notify.notify_webhook("https://bad.host", {})
    assert result.ok is False
    assert result.error is not None


# --- file channel ---

def test_notify_file_appends_json_line(tmp_path):
    log = tmp_path / "events.log"
    payload = {"event": "push", "version": 1}
    result = notify.notify_file(log, payload)
    assert result.ok is True
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "push"


def test_notify_file_appends_multiple_lines(tmp_path):
    log = tmp_path / "events.log"
    notify.notify_file(log, {"event": "lock", "version": 1})
    notify.notify_file(log, {"event": "unlock", "version": 1})
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2


# --- dispatch ---

def test_dispatch_returns_empty_when_no_config(vault_file):
    results = notify.dispatch(vault_file, "lock", 1)
    assert results == []


def test_dispatch_calls_file_channel(vault_file, tmp_path):
    log = tmp_path / "notify.log"
    notify.save_config(vault_file, {"log_file": str(log)})
    results = notify.dispatch(vault_file, "push", 2, note="deploy")
    assert len(results) == 1
    assert results[0].channel == "file"
    assert results[0].ok is True


def test_dispatch_calls_webhook_channel(vault_file):
    notify.save_config(vault_file, {"webhook": "https://example.com/hook"})
    mock_resp = MagicMock(status=204, __enter__=lambda s: s, __exit__=MagicMock(return_value=False))
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = notify.dispatch(vault_file, "rotate", 3)
    assert len(results) == 1
    assert results[0].channel == "webhook"
