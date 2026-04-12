"""Tests for envault.lint."""

import pytest
from envault.lint import lint_env, format_lint_results, LintIssue


SIMPLE_PAIRS = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}


def test_clean_env_returns_no_issues():
    result = lint_env(SIMPLE_PAIRS)
    assert result.issues == []
    assert result.ok is True


def test_empty_value_produces_warning():
    result = lint_env({"API_KEY": ""})
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_empty_value_is_warning_not_error():
    result = lint_env({"API_KEY": ""})
    assert result.ok is True  # warnings don't fail
    assert any(i.severity == "warning" for i in result.issues)


def test_duplicate_key_produces_error():
    raw = ["FOO=bar", "BAZ=qux", "FOO=other"]
    result = lint_env({"FOO": "other", "BAZ": "qux"}, raw_lines=raw)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_duplicate_key_marks_result_not_ok():
    raw = ["FOO=bar", "FOO=other"]
    result = lint_env({"FOO": "other"}, raw_lines=raw)
    assert result.ok is False


def test_lowercase_key_produces_warning():
    result = lint_env({"myKey": "value"})
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_upper_snake_case_key_no_naming_warning():
    result = lint_env({"MY_KEY_123": "value"})
    naming_issues = [i for i in result.issues if i.code == "W002"]
    assert naming_issues == []


def test_whitespace_value_produces_warning():
    result = lint_env({"KEY": "  value  "})
    codes = [i.code for i in result.issues]
    assert "W003" in codes


def test_errors_and_warnings_properties():
    raw = ["foo=bar", "foo=baz"]
    result = lint_env({"foo": "baz"}, raw_lines=raw)
    assert len(result.errors) >= 1
    assert all(i.severity == "error" for i in result.errors)
    assert all(i.severity == "warning" for i in result.warnings)


def test_format_no_issues():
    result = lint_env(SIMPLE_PAIRS)
    output = format_lint_results(result)
    assert output == "No issues found."


def test_format_includes_code_and_severity():
    result = lint_env({"API_KEY": ""})
    output = format_lint_results(result)
    assert "W001" in output
    assert "WARNING" in output


def test_multiple_issues_all_appear_in_output():
    pairs = {"api_key": "", "SECRET ": "  val  "}
    result = lint_env(pairs)
    output = format_lint_results(result)
    assert output.count("\n") >= 1  # at least two lines
