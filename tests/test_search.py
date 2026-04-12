"""Tests for envault.search."""

import pytest

from envault.search import (
    SearchResult,
    format_results,
    search_all,
    search_keys,
    search_values,
)

SAMPLE: dict = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "REDIS_URL": "redis://localhost:6379",
    "SECRET_KEY": "supersecret",
    "DEBUG": "true",
    "API_KEY": "abc123",
}


def test_search_keys_regex_match():
    results = search_keys(SAMPLE, r"URL$")
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL", "REDIS_URL"}


def test_search_keys_case_insensitive_by_default():
    results = search_keys(SAMPLE, r"secret")
    assert any(r.key == "SECRET_KEY" for r in results)


def test_search_keys_case_sensitive_no_match():
    results = search_keys(SAMPLE, r"secret", case_sensitive=True)
    assert results == []


def test_search_keys_glob():
    results = search_keys(SAMPLE, "*_KEY", glob=True)
    keys = {r.key for r in results}
    assert keys == {"SECRET_KEY", "API_KEY"}


def test_search_keys_matched_by_is_key():
    results = search_keys(SAMPLE, "DEBUG")
    assert all(r.matched_by == "key" for r in results)


def test_search_values_regex_match():
    results = search_values(SAMPLE, r"localhost")
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL", "REDIS_URL"}


def test_search_values_glob():
    results = search_values(SAMPLE, "*secret*", glob=True)
    assert any(r.key == "SECRET_KEY" for r in results)


def test_search_values_matched_by_is_value():
    results = search_values(SAMPLE, "true")
    assert all(r.matched_by == "value" for r in results)


def test_search_all_both_tag():
    # "URL" appears in both key names and values
    results = search_all(SAMPLE, r"url", case_sensitive=False)
    both = [r for r in results if r.matched_by == "both"]
    assert len(both) == 2  # DATABASE_URL and REDIS_URL


def test_search_all_key_only_tag():
    results = search_all(SAMPLE, r"DEBUG")
    match = next(r for r in results if r.key == "DEBUG")
    assert match.matched_by == "key"


def test_search_all_empty_env():
    assert search_all({}, "anything") == []


def test_format_results_no_matches():
    assert format_results([]) == "No matches found."


def test_format_results_contains_key():
    results = [SearchResult(key="FOO", value="bar", matched_by="key")]
    output = format_results(results)
    assert "FOO" in output
    assert "bar" in output


def test_format_results_hide_values():
    results = [SearchResult(key="FOO", value="bar", matched_by="key")]
    output = format_results(results, show_values=False)
    assert "FOO" in output
    assert "bar" not in output


def test_format_results_shows_matched_by_tag():
    results = [SearchResult(key="FOO", value="bar", matched_by="both")]
    output = format_results(results)
    assert "both" in output
