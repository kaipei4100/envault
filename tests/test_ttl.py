"""Tests for envault.ttl."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.ttl import (
    _ttl_path,
    delete_ttl,
    expired_keys,
    expiring_soon,
    get_ttl,
    list_ttls,
    set_ttl,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "my.vault"
    p.write_bytes(b"dummy")
    return p


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


# ---------------------------------------------------------------------------
# _ttl_path
# ---------------------------------------------------------------------------

def test_ttl_path_is_sibling_of_vault(vault_file: Path) -> None:
    assert _ttl_path(vault_file).parent == vault_file.parent


def test_ttl_path_filename(vault_file: Path) -> None:
    assert _ttl_path(vault_file).name == ".envault_ttl.json"


# ---------------------------------------------------------------------------
# set / get
# ---------------------------------------------------------------------------

def test_set_ttl_creates_sidecar_file(vault_file: Path) -> None:
    set_ttl(vault_file, "API_KEY", _future())
    assert _ttl_path(vault_file).exists()


def test_get_ttl_returns_datetime(vault_file: Path) -> None:
    expiry = _future()
    set_ttl(vault_file, "API_KEY", expiry)
    result = get_ttl(vault_file, "API_KEY")
    assert isinstance(result, datetime)
    # Compare with second precision
    assert abs((result - expiry).total_seconds()) < 1


def test_get_ttl_missing_key_returns_none(vault_file: Path) -> None:
    assert get_ttl(vault_file, "MISSING") is None


def test_set_ttl_stores_utc(vault_file: Path) -> None:
    expiry = _future()
    set_ttl(vault_file, "DB_PASS", expiry)
    raw = json.loads(_ttl_path(vault_file).read_text())
    assert "+00:00" in raw["DB_PASS"] or "Z" in raw["DB_PASS"]


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_ttl_returns_true_when_key_existed(vault_file: Path) -> None:
    set_ttl(vault_file, "TOKEN", _future())
    assert delete_ttl(vault_file, "TOKEN") is True


def test_delete_ttl_removes_key(vault_file: Path) -> None:
    set_ttl(vault_file, "TOKEN", _future())
    delete_ttl(vault_file, "TOKEN")
    assert get_ttl(vault_file, "TOKEN") is None


def test_delete_ttl_returns_false_when_key_missing(vault_file: Path) -> None:
    assert delete_ttl(vault_file, "NOPE") is False


# ---------------------------------------------------------------------------
# list_ttls
# ---------------------------------------------------------------------------

def test_list_ttls_returns_all_keys(vault_file: Path) -> None:
    set_ttl(vault_file, "A", _future(100))
    set_ttl(vault_file, "B", _future(200))
    result = list_ttls(vault_file)
    assert set(result.keys()) == {"A", "B"}


def test_list_ttls_empty_when_no_sidecar(vault_file: Path) -> None:
    assert list_ttls(vault_file) == {}


# ---------------------------------------------------------------------------
# expired_keys
# ---------------------------------------------------------------------------

def test_expired_keys_returns_past_keys(vault_file: Path) -> None:
    set_ttl(vault_file, "OLD", _past(7200))
    set_ttl(vault_file, "NEW", _future(3600))
    assert expired_keys(vault_file) == ["OLD"]


def test_expired_keys_empty_when_all_future(vault_file: Path) -> None:
    set_ttl(vault_file, "K", _future(3600))
    assert expired_keys(vault_file) == []


# ---------------------------------------------------------------------------
# expiring_soon
# ---------------------------------------------------------------------------

def test_expiring_soon_detects_key_within_window(vault_file: Path) -> None:
    set_ttl(vault_file, "SOON", _future(600))
    results = expiring_soon(vault_file, within_seconds=3600)
    keys = [k for k, _ in results]
    assert "SOON" in keys


def test_expiring_soon_excludes_distant_keys(vault_file: Path) -> None:
    set_ttl(vault_file, "FAR", _future(86_400 * 30))
    results = expiring_soon(vault_file, within_seconds=3600)
    assert results == []


def test_expiring_soon_excludes_already_expired(vault_file: Path) -> None:
    set_ttl(vault_file, "GONE", _past(60))
    results = expiring_soon(vault_file, within_seconds=3600)
    assert results == []
