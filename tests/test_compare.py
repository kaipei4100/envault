"""Tests for envault.compare."""
from __future__ import annotations

import pytest

from envault.vault import write_vault
from envault.snapshot import save_snapshot
from envault.compare import compare_versions, format_compare


PASSWORD = "compare-secret"


@pytest.fixture()
def vault_file(tmp_path):
    vf = tmp_path / "test.vault"
    env_v1 = {"HOST": "localhost", "PORT": "5432", "OLD_KEY": "gone"}
    write_vault(str(vf), env_v1, PASSWORD)
    save_snapshot(str(vf), PASSWORD, version=1)

    env_v2 = {"HOST": "prod.example.com", "PORT": "5432", "NEW_KEY": "hello"}
    write_vault(str(vf), env_v2, PASSWORD)
    save_snapshot(str(vf), PASSWORD, version=2)
    return str(vf)


def test_compare_returns_compare_result(vault_file):
    from envault.compare import CompareResult
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    assert isinstance(result, CompareResult)


def test_compare_version_fields(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    assert result.version_a == 1
    assert result.version_b == 2


def test_compare_vault_path_stored(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    assert result.vault_path == vault_file


def test_compare_detects_added_key(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    added_keys = [d.key for d in result.added]
    assert "NEW_KEY" in added_keys


def test_compare_detects_removed_key(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    removed_keys = [d.key for d in result.removed]
    assert "OLD_KEY" in removed_keys


def test_compare_detects_changed_key(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    changed_keys = [d.key for d in result.changed]
    assert "HOST" in changed_keys


def test_compare_unchanged_key_not_in_added_removed_changed(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    all_modified = {d.key for d in result.added + result.removed + result.changed}
    assert "PORT" not in all_modified


def test_compare_ok_false_when_differences(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    assert result.ok is False


def test_compare_ok_true_when_identical(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 1)
    assert result.ok is True


def test_format_compare_contains_version_header(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    text = format_compare(result)
    assert "v1" in text
    assert "v2" in text


def test_format_compare_shows_added_with_plus(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    text = format_compare(result)
    assert "+ NEW_KEY" in text


def test_format_compare_shows_removed_with_minus(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 2)
    text = format_compare(result)
    assert "- OLD_KEY" in text


def test_format_compare_no_differences_message_when_same(vault_file):
    result = compare_versions(vault_file, PASSWORD, 1, 1)
    text = format_compare(result)
    assert "no differences" in text
