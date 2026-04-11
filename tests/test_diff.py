"""Tests for envault.diff module."""

import pytest

from envault.diff import DiffLine, build_diff, format_diff


OLD = {"FOO": "bar", "KEEP": "same", "GONE": "bye"}
NEW = {"FOO": "baz", "KEEP": "same", "ADDED": "hello"}


def test_build_diff_detects_added():
    lines = build_diff(OLD, NEW)
    added = [l for l in lines if l.kind == "added"]
    assert any(l.key == "ADDED" for l in added)


def test_build_diff_detects_removed():
    lines = build_diff(OLD, NEW)
    removed = [l for l in lines if l.kind == "removed"]
    assert any(l.key == "GONE" for l in removed)


def test_build_diff_detects_changed():
    lines = build_diff(OLD, NEW)
    changed = [l for l in lines if l.kind == "changed"]
    assert any(l.key == "FOO" for l in changed)


def test_build_diff_detects_unchanged():
    lines = build_diff(OLD, NEW)
    unchanged = [l for l in lines if l.kind == "unchanged"]
    assert any(l.key == "KEEP" for l in unchanged)


def test_build_diff_changed_stores_both_values():
    lines = build_diff(OLD, NEW)
    changed = next(l for l in lines if l.key == "FOO")
    assert changed.old_value == "bar"
    assert changed.new_value == "baz"


def test_format_diff_no_changes_returns_message():
    result = format_diff({"A": "1"}, {"A": "1"})
    assert "no changes" in result


def test_format_diff_masks_values_by_default():
    result = format_diff(OLD, NEW, show_values=True, mask=True)
    assert "bar" not in result
    assert "***" in result


def test_format_diff_shows_values_when_unmasked():
    result = format_diff(OLD, NEW, show_values=True, mask=False)
    assert "baz" in result


def test_format_diff_hides_unchanged_by_default():
    result = format_diff(OLD, NEW)
    assert "KEEP" not in result


def test_format_diff_includes_unchanged_when_requested():
    result = format_diff(OLD, NEW, skip_unchanged=False)
    assert "KEEP" in result


def test_diffline_added_format_prefix():
    line = DiffLine("added", "NEW_KEY", new_value="val")
    assert line.format().startswith("  +")


def test_diffline_removed_format_prefix():
    line = DiffLine("removed", "OLD_KEY", old_value="val")
    assert line.format().startswith("  -")


def test_diffline_changed_format_prefix():
    line = DiffLine("changed", "KEY", old_value="a", new_value="b")
    assert line.format().startswith("  ~")


def test_build_diff_empty_old_all_added():
    lines = build_diff({}, {"X": "1", "Y": "2"})
    assert all(l.kind == "added" for l in lines)


def test_build_diff_empty_new_all_removed():
    lines = build_diff({"X": "1", "Y": "2"}, {})
    assert all(l.kind == "removed" for l in lines)
