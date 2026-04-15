"""Tests for envault.redact."""
import pytest
from envault.redact import (
    RedactResult,
    is_sensitive,
    mask_value,
    redact_env,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert is_sensitive("PASSWORD") is True

def test_is_sensitive_api_key_variants():
    for key in ("API_KEY", "APIKEY", "api-key"):
        assert is_sensitive(key) is True, key

def test_is_sensitive_token():
    assert is_sensitive("ACCESS_TOKEN") is True

def test_is_sensitive_secret():
    assert is_sensitive("DB_SECRET") is True

def test_is_sensitive_safe_key():
    assert is_sensitive("APP_NAME") is False

def test_is_sensitive_port():
    assert is_sensitive("PORT") is False


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_full():
    assert mask_value("supersecret") == "***********"

def test_mask_value_empty_returns_empty():
    assert mask_value("") == ""

def test_mask_value_partial_long_enough():
    result = mask_value("supersecret", partial=True)
    assert result.startswith("su")
    assert result.endswith("et")
    assert "*" in result

def test_mask_value_partial_too_short_falls_back_to_full():
    result = mask_value("abc", partial=True)
    assert result == "***"

def test_mask_value_partial_length_preserved():
    value = "abcdefghij"
    result = mask_value(value, partial=True)
    assert len(result) == len(value)


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_redact_env_returns_redact_result():
    result = redact_env({"APP_NAME": "myapp", "SECRET_KEY": "abc123"})
    assert isinstance(result, RedactResult)

def test_redact_env_masks_sensitive_keys():
    result = redact_env({"DB_PASSWORD": "hunter2", "HOST": "localhost"})
    assert result.redacted["DB_PASSWORD"] == "*" * len("hunter2")
    assert result.redacted["HOST"] == "localhost"

def test_redact_env_safe_keys_unchanged():
    env = {"PORT": "5432", "APP_NAME": "envault"}
    result = redact_env(env)
    assert result.redacted == env

def test_redact_env_records_redacted_keys():
    result = redact_env({"API_KEY": "xyz", "NAME": "test"})
    assert "API_KEY" in result.redacted_keys
    assert "NAME" not in result.redacted_keys

def test_redact_env_extra_keys():
    result = redact_env({"MY_CUSTOM": "value"}, extra_keys=["MY_CUSTOM"])
    assert result.redacted["MY_CUSTOM"] == "*" * len("value")
    assert "MY_CUSTOM" in result.redacted_keys

def test_redact_env_extra_keys_case_insensitive():
    result = redact_env({"MY_CUSTOM": "value"}, extra_keys=["my_custom"])
    assert result.redacted["MY_CUSTOM"] == "*" * len("value")

def test_redact_env_original_unchanged():
    env = {"SECRET": "shh"}
    result = redact_env(env)
    assert result.original["SECRET"] == "shh"

def test_redact_env_partial_mode():
    result = redact_env({"API_KEY": "abcdefghij"}, partial=True)
    val = result.redacted["API_KEY"]
    assert val[0:2] == "ab"
    assert val[-2:] == "ij"

def test_redact_env_ok_true_when_keys_redacted():
    result = redact_env({"PASSWORD": "secret"})
    assert result.ok is True

def test_redact_env_ok_false_when_nothing_redacted():
    result = redact_env({"HOST": "localhost"})
    assert result.ok is False
