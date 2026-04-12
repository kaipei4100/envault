"""Tests for envault.export."""

from __future__ import annotations

import json

import pytest

from envault.export import export_docker, export_env, export_json, export_shell

SAMPLE: dict[str, str] = {
    "DATABASE_URL": "postgres://localhost/db",
    "SECRET_KEY": "s3cr3t with spaces",
    "DEBUG": "true",
}


# ---------------------------------------------------------------------------
# export_shell
# ---------------------------------------------------------------------------

def test_export_shell_contains_export_keyword():
    out = export_shell(SAMPLE)
    for line in out.splitlines():
        assert line.startswith("export ")


def test_export_shell_no_export_keyword():
    out = export_shell(SAMPLE, export_keyword=False)
    for line in out.splitlines():
        assert not line.startswith("export ")


def test_export_shell_quotes_spaces():
    out = export_shell({"KEY": "hello world"})
    assert "'hello world'" in out or '"hello world"' in out or "hello\\ world" in out


def test_export_shell_sorted_keys():
    keys = [line.split("=")[0].replace("export ", "") for line in export_shell(SAMPLE).splitlines()]
    assert keys == sorted(keys)


def test_export_shell_empty_env():
    assert export_shell({}) == ""


# ---------------------------------------------------------------------------
# export_docker
# ---------------------------------------------------------------------------

def test_export_docker_uses_env_flag():
    out = export_docker(SAMPLE)
    for line in out.splitlines():
        assert line.startswith("--env ")


def test_export_docker_empty_env():
    assert export_docker({}) == ""


def test_export_docker_sorted_keys():
    keys = [line.split("=")[0].replace("--env ", "") for line in export_docker(SAMPLE).splitlines()]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

def test_export_json_valid_json():
    out = export_json(SAMPLE)
    parsed = json.loads(out)
    assert parsed == SAMPLE


def test_export_json_sorted_keys():
    out = export_json(SAMPLE)
    parsed = json.loads(out)
    assert list(parsed.keys()) == sorted(parsed.keys())


# ---------------------------------------------------------------------------
# export_env dispatcher
# ---------------------------------------------------------------------------

def test_export_env_dispatches_shell():
    assert export_env(SAMPLE, "shell") == export_shell(SAMPLE)


def test_export_env_dispatches_docker():
    assert export_env(SAMPLE, "docker") == export_docker(SAMPLE)


def test_export_env_dispatches_json():
    assert export_env(SAMPLE, "json") == export_json(SAMPLE)


def test_export_env_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown export format"):
        export_env(SAMPLE, "yaml")  # type: ignore[arg-type]
