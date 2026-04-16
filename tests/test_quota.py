"""Tests for envault.quota."""
import pytest
from pathlib import Path
from envault.quota import (
    set_quota,
    get_quota,
    delete_quota,
    current_usage,
    check_quota,
    QuotaExceeded,
)


@pytest.fixture
def vault_file(tmp_path):
    vf = tmp_path / "test.vault"
    vf.write_bytes(b"x" * 200)
    return vf


def test_get_quota_returns_none_when_unset(vault_file):
    assert get_quota(vault_file) is None


def test_set_quota_persists_value(vault_file):
    set_quota(vault_file, 1024)
    assert get_quota(vault_file) == 1024


def test_set_quota_returns_dict_with_max_bytes(vault_file):
    result = set_quota(vault_file, 512)
    assert result["max_bytes"] == 512


def test_set_quota_overwrites_previous(vault_file):
    set_quota(vault_file, 1024)
    set_quota(vault_file, 2048)
    assert get_quota(vault_file) == 2048


def test_delete_quota_removes_setting(vault_file):
    set_quota(vault_file, 1024)
    deleted = delete_quota(vault_file)
    assert deleted is True
    assert get_quota(vault_file) is None


def test_delete_quota_returns_false_when_not_set(vault_file):
    assert delete_quota(vault_file) is False


def test_current_usage_counts_non_hidden_files(vault_file):
    usage = current_usage(vault_file)
    assert usage >= 200


def test_current_usage_excludes_dot_files(vault_file):
    hidden = vault_file.parent / ".quota.json"
    hidden.write_bytes(b"z" * 500)
    usage = current_usage(vault_file)
    # hidden file should not be counted
    assert usage == 200


def test_check_quota_no_limit_passes(vault_file):
    result = check_quota(vault_file)
    assert result["exceeded"] is False
    assert result["limit_bytes"] is None


def test_check_quota_within_limit_passes(vault_file):
    set_quota(vault_file, 10_000)
    result = check_quota(vault_file)
    assert result["exceeded"] is False


def test_check_quota_exceeded_raises(vault_file):
    set_quota(vault_file, 10)  # 10 bytes, file is 200
    with pytest.raises(QuotaExceeded) as exc_info:
        check_quota(vault_file)
    assert exc_info.value.limit == 10
    assert exc_info.value.used >= 200


def test_quota_exceeded_str_includes_sizes(vault_file):
    set_quota(vault_file, 10)
    with pytest.raises(QuotaExceeded) as exc_info:
        check_quota(vault_file)
    msg = str(exc_info.value)
    assert "10" in msg
    assert "exceeded" in msg.lower()
