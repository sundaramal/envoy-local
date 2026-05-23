"""Integration tests for retry policy round-trip and CLI interaction."""

import json
import pytest

from envoy_local.retry_policy import RetryPolicy, validate_retry_policy
from envoy_local.cli_retry import cmd_retry_validate, cmd_retry_show


def _make_args(**kwargs):
    class Args:
        pass
    a = Args()
    defaults = {"file": None, "json": "{}", "output": "text"}
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(a, k, v)
    return a


def test_round_trip_to_dict_and_back():
    original = RetryPolicy(
        retry_on=["5xx", "connect-failure"],
        num_retries=5,
        per_try_timeout_ms=100,
    )
    d = original.to_dict()
    restored = RetryPolicy.from_dict(d)
    assert restored.retry_on == original.retry_on
    assert restored.num_retries == original.num_retries
    assert restored.per_try_timeout_ms == original.per_try_timeout_ms


def test_full_flow_valid_policy_text(capsys):
    payload = {"retry_on": "5xx,reset", "num_retries": 3, "per_try_timeout": "200ms"}
    args = _make_args(json=json.dumps(payload), output="text")
    cmd_retry_validate(args)
    out = capsys.readouterr().out
    assert "valid" in out.lower()


def test_full_flow_invalid_policy_json_output(capsys):
    payload = {"retry_on": "unknown-cond", "num_retries": -1}
    args = _make_args(json=json.dumps(payload), output="json")
    with pytest.raises(SystemExit):
        cmd_retry_validate(args)
    # When output=json and invalid, it still prints JSON before exiting
    # (the current impl prints then exits only for text mode)
    # Re-test with text to confirm exit code 2
    args2 = _make_args(json=json.dumps(payload), output="text")
    with pytest.raises(SystemExit) as exc_info:
        cmd_retry_validate(args2)
    assert exc_info.value.code == 2


def test_show_includes_timeout_field(capsys):
    payload = {"retry_on": "5xx", "per_try_timeout": "1s"}
    args = _make_args(json=json.dumps(payload))
    cmd_retry_show(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["per_try_timeout"] == "1000ms"


def test_show_omits_timeout_when_absent(capsys):
    payload = {"retry_on": "5xx"}
    args = _make_args(json=json.dumps(payload))
    cmd_retry_show(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "per_try_timeout" not in data
