"""Tests for circuit_breaker module and cli_circuit_breaker commands."""

import json
import sys
import pytest
from unittest.mock import patch, mock_open
from envoy_local.circuit_breaker import (
    CircuitBreakerThresholds,
    validate_circuit_breaker,
    format_circuit_breaker_report,
)
from envoy_local.cli_circuit_breaker import cmd_cb_validate, cmd_cb_show


# --- Unit tests: CircuitBreakerThresholds ---

def test_default_thresholds_are_valid():
    t = CircuitBreakerThresholds()
    result = validate_circuit_breaker(t)
    assert result.is_valid


def test_to_dict_contains_all_required_keys():
    t = CircuitBreakerThresholds()
    d = t.to_dict()
    assert "max_connections" in d
    assert "max_pending_requests" in d
    assert "max_requests" in d
    assert "max_retries" in d


def test_to_dict_omits_max_connection_pools_when_none():
    t = CircuitBreakerThresholds(max_connection_pools=None)
    assert "max_connection_pools" not in t.to_dict()


def test_to_dict_includes_max_connection_pools_when_set():
    t = CircuitBreakerThresholds(max_connection_pools=50)
    assert t.to_dict()["max_connection_pools"] == 50


def test_from_dict_round_trip():
    original = CircuitBreakerThresholds(max_connections=512, max_retries=5)
    restored = CircuitBreakerThresholds.from_dict(original.to_dict())
    assert restored.max_connections == 512
    assert restored.max_retries == 5


def test_zero_max_connections_is_invalid():
    t = CircuitBreakerThresholds(max_connections=0)
    result = validate_circuit_breaker(t)
    assert not result.is_valid
    assert any(e.field == "max_connections" for e in result.errors)


def test_negative_max_retries_is_invalid():
    t = CircuitBreakerThresholds(max_retries=-1)
    result = validate_circuit_breaker(t)
    assert not result.is_valid
    assert any(e.field == "max_retries" for e in result.errors)


def test_zero_max_connection_pools_is_invalid():
    t = CircuitBreakerThresholds(max_connection_pools=0)
    result = validate_circuit_breaker(t)
    assert not result.is_valid


def test_format_report_shows_ok_for_valid():
    t = CircuitBreakerThresholds()
    result = validate_circuit_breaker(t)
    report = format_circuit_breaker_report(t, result)
    assert "OK" in report


def test_format_report_shows_failed_for_invalid():
    t = CircuitBreakerThresholds(max_connections=0)
    result = validate_circuit_breaker(t)
    report = format_circuit_breaker_report(t, result)
    assert "FAILED" in report
    assert "max_connections" in report


# --- CLI tests ---

class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_cmd_cb_show_prints_text(capsys):
    args = _Args(json=False)
    cmd_cb_show(args)
    out = capsys.readouterr().out
    assert "max_connections" in out


def test_cmd_cb_show_json_output(capsys):
    args = _Args(json=True)
    cmd_cb_show(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "max_connections" in data


def test_cmd_cb_validate_valid_config(capsys, tmp_path):
    cfg = {"max_connections": 256, "max_pending_requests": 256, "max_requests": 256, "max_retries": 2}
    p = tmp_path / "cb.json"
    p.write_text(json.dumps(cfg))
    args = _Args(config=str(p), json=False)
    cmd_cb_validate(args)  # should not raise
    out = capsys.readouterr().out
    assert "OK" in out


def test_cmd_cb_validate_invalid_exits(tmp_path):
    cfg = {"max_connections": 0}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(cfg))
    args = _Args(config=str(p), json=False)
    with pytest.raises(SystemExit) as exc:
        cmd_cb_validate(args)
    assert exc.value.code == 2


def test_cmd_cb_validate_file_not_found_exits():
    args = _Args(config="/nonexistent/path.json", json=False)
    with pytest.raises(SystemExit) as exc:
        cmd_cb_validate(args)
    assert exc.value.code == 1
