"""Tests for envault.parser — .env parsing and serialisation."""

import pytest

from envault.parser import diff_envs, parse_env, serialise_env


def test_parse_simple_pairs():
    text = "FOO=bar\nBAZ=qux\n"
    assert parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_ignores_comments():
    text = "# comment\nKEY=value\n"
    result = parse_env(text)
    assert "#" not in str(result)
    assert result == {"KEY": "value"}


def test_parse_ignores_blank_lines():
    text = "\nA=1\n\nB=2\n"
    assert parse_env(text) == {"A": "1", "B": "2"}


def test_parse_double_quoted_value():
    assert parse_env('KEY="hello world"') == {"KEY": "hello world"}


def test_parse_single_quoted_value():
    assert parse_env("KEY='hello world'") == {"KEY": "hello world"}


def test_parse_export_prefix():
    assert parse_env("export MY_VAR=123") == {"MY_VAR": "123"}


def test_parse_empty_string():
    assert parse_env("") == {}


def test_serialise_roundtrip():
    original = {"HOST": "localhost", "PORT": "5432"}
    text = serialise_env(original)
    assert parse_env(text) == original


def test_serialise_quotes_values_with_spaces():
    text = serialise_env({"MSG": "hello world"})
    assert '"hello world"' in text


def test_diff_detects_added():
    added, removed, changed = diff_envs({"A": "1"}, {"A": "1", "B": "2"})
    assert added == {"B": "2"}
    assert removed == []
    assert changed == {}


def test_diff_detects_removed():
    added, removed, changed = diff_envs({"A": "1", "B": "2"}, {"A": "1"})
    assert added == {}
    assert "B" in removed
    assert changed == {}


def test_diff_detects_changed():
    added, removed, changed = diff_envs({"A": "old"}, {"A": "new"})
    assert changed == {"A": ("old", "new")}


def test_diff_identical_envs():
    env = {"X": "1", "Y": "2"}
    added, removed, changed = diff_envs(env, env.copy())
    assert added == {} and removed == [] and changed == {}
