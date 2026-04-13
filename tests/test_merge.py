"""Tests for envault.merge."""

import pytest

from envault.merge import (
    ConflictStrategy,
    MergeConflict,
    MergeConflictError,
    MergeResult,
    merge_envs,
)

BASE = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
INCOMING = {"HOST": "prod.example.com", "PORT": "5432", "NEW_KEY": "hello"}


def test_added_keys_always_included():
    result = merge_envs(BASE, INCOMING)
    assert "NEW_KEY" in result.env
    assert result.env["NEW_KEY"] == "hello"
    assert "NEW_KEY" in result.added


def test_unchanged_keys_preserved():
    result = merge_envs(BASE, INCOMING)
    assert result.env["PORT"] == "5432"
    assert "PORT" not in result.updated
    assert "PORT" not in result.added


def test_keys_only_in_base_listed_as_removed():
    result = merge_envs(BASE, INCOMING)
    assert "DEBUG" in result.removed


def test_strategy_ours_keeps_base_value():
    result = merge_envs(BASE, INCOMING, strategy=ConflictStrategy.OURS)
    assert result.env["HOST"] == "localhost"
    assert result.updated == []


def test_strategy_ours_records_conflict():
    result = merge_envs(BASE, INCOMING, strategy=ConflictStrategy.OURS)
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "HOST"


def test_strategy_theirs_overwrites_base_value():
    result = merge_envs(BASE, INCOMING, strategy=ConflictStrategy.THEIRS)
    assert result.env["HOST"] == "prod.example.com"
    assert "HOST" in result.updated


def test_strategy_theirs_still_records_conflict():
    result = merge_envs(BASE, INCOMING, strategy=ConflictStrategy.THEIRS)
    assert any(c.key == "HOST" for c in result.conflicts)


def test_strategy_error_raises_on_conflict():
    with pytest.raises(MergeConflictError) as exc_info:
        merge_envs(BASE, INCOMING, strategy=ConflictStrategy.ERROR)
    assert exc_info.value.conflicts[0].key == "HOST"


def test_strategy_error_collects_all_conflicts():
    incoming = {"HOST": "other", "PORT": "9999"}
    with pytest.raises(MergeConflictError) as exc_info:
        merge_envs(BASE, incoming, strategy=ConflictStrategy.ERROR)
    keys = {c.key for c in exc_info.value.conflicts}
    assert keys == {"HOST", "PORT"}


def test_ok_is_false_when_error_strategy_and_conflicts():
    result = merge_envs(BASE, INCOMING, strategy=ConflictStrategy.OURS)
    # OURS strategy with conflicts is still ok (resolved)
    assert result.ok is True


def test_no_conflicts_when_envs_identical():
    result = merge_envs(BASE, BASE)
    assert result.conflicts == []
    assert result.ok is True


def test_exclude_keys_skips_incoming_key():
    result = merge_envs(BASE, INCOMING, exclude_keys=["HOST", "NEW_KEY"])
    assert result.env["HOST"] == "localhost"  # not overwritten
    assert "NEW_KEY" not in result.env


def test_merge_result_env_is_new_dict():
    result = merge_envs(BASE, INCOMING)
    result.env["EXTRA"] = "x"
    assert "EXTRA" not in BASE


def test_conflict_str_contains_key_and_values():
    c = MergeConflict("FOO", "bar", "baz")
    s = str(c)
    assert "FOO" in s
    assert "bar" in s
    assert "baz" in s


def test_merge_conflict_error_message_lists_conflicts():
    conflicts = [MergeConflict("A", "1", "2"), MergeConflict("B", "x", "y")]
    err = MergeConflictError(conflicts)
    msg = str(err)
    assert "A" in msg
    assert "B" in msg
