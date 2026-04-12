"""Tests for envault.template."""

from pathlib import Path

import pytest

from envault.template import (
    RenderResult,
    list_placeholders,
    render_file,
    render_string,
)


ENV = {"APP_HOST": "localhost", "APP_PORT": "8080", "SECRET": "s3cr3t"}


# ---------------------------------------------------------------------------
# render_string
# ---------------------------------------------------------------------------

def test_render_string_substitutes_known_key():
    result = render_string("host={{ APP_HOST }}", ENV)
    assert result.text == "host=localhost"


def test_render_string_multiple_keys():
    result = render_string("{{ APP_HOST }}:{{ APP_PORT }}", ENV)
    assert result.text == "localhost:8080"


def test_render_string_records_substituted_keys():
    result = render_string("{{ APP_HOST }}:{{ APP_PORT }}", ENV)
    assert set(result.substituted) == {"APP_HOST", "APP_PORT"}


def test_render_string_missing_key_left_as_is():
    result = render_string("{{ UNKNOWN }}", ENV)
    assert result.text == "{{ UNKNOWN }}"


def test_render_string_records_missing_keys():
    result = render_string("{{ MISSING_A }} {{ MISSING_B }}", ENV)
    assert "MISSING_A" in result.missing
    assert "MISSING_B" in result.missing


def test_render_string_ok_true_when_no_missing():
    result = render_string("{{ APP_HOST }}", ENV)
    assert result.ok is True


def test_render_string_ok_false_when_missing():
    result = render_string("{{ NOPE }}", ENV)
    assert result.ok is False


def test_render_string_no_placeholders():
    result = render_string("plain text", ENV)
    assert result.text == "plain text"
    assert result.substituted == []
    assert result.missing == []


def test_render_string_whitespace_inside_braces():
    result = render_string("{{  SECRET  }}", ENV)
    assert result.text == "s3cr3t"


# ---------------------------------------------------------------------------
# render_file
# ---------------------------------------------------------------------------

def test_render_file_reads_template(tmp_path: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("port={{ APP_PORT }}")
    result = render_file(tpl, ENV)
    assert result.text == "port=8080"


def test_render_file_writes_output(tmp_path: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("host={{ APP_HOST }}")
    out = tmp_path / "config.txt"
    render_file(tpl, ENV, output_path=out)
    assert out.read_text() == "host=localhost"


def test_render_file_no_output_path_does_not_create_file(tmp_path: Path):
    tpl = tmp_path / "config.tpl"
    tpl.write_text("{{ APP_HOST }}")
    render_file(tpl, ENV)
    assert list(tmp_path.iterdir()) == [tpl]


# ---------------------------------------------------------------------------
# list_placeholders
# ---------------------------------------------------------------------------

def test_list_placeholders_returns_keys():
    assert list_placeholders("{{ A }} {{ B }}") == ["A", "B"]


def test_list_placeholders_deduplicates():
    keys = list_placeholders("{{ A }} {{ A }} {{ B }}")
    assert keys == ["A", "B"]


def test_list_placeholders_empty_template():
    assert list_placeholders("no placeholders here") == []
