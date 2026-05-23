"""Tests for timeout_policy and cli_timeout modules."""

import json
import sys
import pytest
from unittest.mock import patch
from types import SimpleNamespace

from envoy_local.timeout_policy import (
    TimeoutPolicy,
    to_dict,
    from_dict,
    validate_timeout_policy,
)
from envoy_local.cli_timeout import cmd_timeout_validate, cmd_timeout_show


# --- timeout_policy unit tests ---

def test_default_policy_is_valid():
    policy = TimeoutPolicy()
    result = validate_timeout_policy(policy)
    assert result.is_valid
    assert result.errors == []
    assert result.warnings == []


def test_zero_connect_timeout_is_error():
    policy = TimeoutPolicy(connect_timeout_ms=0)
    result = validate_timeout_policy(policy)
    assert not result.is_valid
    assert any("connect_timeout_ms" in e for e in result.errors)


def test_large_connect_timeout_produces_warning():
    policy = TimeoutPolicy(connect_timeout_ms=90_000)
    result = validate_timeout_policy(policy)
    assert result.is_valid
    assert any("60s" in w for w in result.warnings)


def test_zero_request_timeout_is_error():
    policy = TimeoutPolicy(request_timeout_ms=0)
    result = validate_timeout_policy(policy)
    assert not result.is_valid
    assert any("request_timeout_ms" in e for e in result.errors)


def test_max_stream_less_than_request_timeout_warns():
    policy = TimeoutPolicy(request_timeout_ms=5000, max_stream_duration_ms=1000)
    result = validate_timeout_policy(policy)
    assert result.is_valid
    assert any("max_stream_duration_ms" in w for w in result.warnings)


def test_to_dict_omits_none_fields():
    policy = TimeoutPolicy(connect_timeout_ms=500)
    d = to_dict(policy)
    assert "connect_timeout_ms" in d
    assert "request_timeout_ms" not in d
    assert "idle_timeout_ms" not in d


def test_to_dict_includes_all_when_set():
    policy = TimeoutPolicy(connect_timeout_ms=500, request_timeout_ms=2000,
                           idle_timeout_ms=3000, max_stream_duration_ms=4000)
    d = to_dict(policy)
    assert d["connect_timeout_ms"] == 500
    assert d["request_timeout_ms"] == 2000
    assert d["idle_timeout_ms"] == 3000
    assert d["max_stream_duration_ms"] == 4000


def test_from_dict_round_trip():
    original = TimeoutPolicy(connect_timeout_ms=300, request_timeout_ms=1500)
    d = to_dict(original)
    restored = from_dict(d)
    assert restored.connect_timeout_ms == 300
    assert restored.request_timeout_ms == 1500
    assert restored.idle_timeout_ms is None


def test_from_dict_uses_defaults_for_missing_keys():
    policy = from_dict({})
    assert policy.connect_timeout_ms == 1000
    assert policy.request_timeout_ms is None


# --- cli_timeout unit tests ---

def _make_args(**kwargs):
    defaults = dict(connect_timeout_ms=1000, request_timeout_ms=None,
                    idle_timeout_ms=None, max_stream_duration_ms=None, json=False)
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_cmd_timeout_validate_valid_prints_ok(capsys):
    cmd_timeout_validate(_make_args())
    out = capsys.readouterr().out
    assert "valid" in out.lower()


def test_cmd_timeout_validate_invalid_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_timeout_validate(_make_args(connect_timeout_ms=-1))
    assert exc.value.code == 1


def test_cmd_timeout_validate_json_output(capsys):
    cmd_timeout_validate(_make_args(json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["valid"] is True
    assert data["errors"] == []


def test_cmd_timeout_show_text(capsys):
    cmd_timeout_show(_make_args(connect_timeout_ms=250))
    out = capsys.readouterr().out
    assert "connect_timeout_ms" in out
    assert "250" in out


def test_cmd_timeout_show_json(capsys):
    cmd_timeout_show(_make_args(connect_timeout_ms=300, json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["connect_timeout_ms"] == 300
