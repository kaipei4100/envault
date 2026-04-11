"""Tests for envault.profiles."""

from __future__ import annotations

import json
import pytest

from envault import profiles as prof


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect profile storage to a temporary directory for every test."""
    config_dir = tmp_path / ".envault"
    monkeypatch.setattr(prof, "_CONFIG_DIR", config_dir)
    monkeypatch.setattr(prof, "_CONFIG_FILE", config_dir / "profiles.json")


_SAMPLE = {"backend": "local", "store_dir": "/tmp/vault", "env": "staging"}


def test_save_and_load_profile():
    prof.save_profile("staging", _SAMPLE)
    result = prof.load_profile("staging")
    assert result == _SAMPLE


def test_load_missing_profile_raises():
    with pytest.raises(KeyError, match="not found"):
        prof.load_profile("nonexistent")


def test_save_overwrites_existing_profile():
    prof.save_profile("dev", {"backend": "local"})
    prof.save_profile("dev", {"backend": "s3", "bucket": "my-bucket"})
    assert prof.load_profile("dev")["backend"] == "s3"


def test_list_profiles_returns_sorted_names():
    prof.save_profile("zebra", {})
    prof.save_profile("alpha", {})
    prof.save_profile("mango", {})
    assert prof.list_profiles() == ["alpha", "mango", "zebra"]


def test_list_profiles_empty_when_no_profiles():
    assert prof.list_profiles() == []


def test_delete_existing_profile_returns_true():
    prof.save_profile("temp", {})
    assert prof.delete_profile("temp") is True
    assert not prof.profile_exists("temp")


def test_delete_missing_profile_returns_false():
    assert prof.delete_profile("ghost") is False


def test_profile_exists_true_and_false():
    prof.save_profile("real", {})
    assert prof.profile_exists("real") is True
    assert prof.profile_exists("fake") is False


def test_config_file_is_valid_json(tmp_path):
    prof.save_profile("ci", {"backend": "s3", "bucket": "ci-bucket"})
    raw = prof._CONFIG_FILE.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "ci" in data
