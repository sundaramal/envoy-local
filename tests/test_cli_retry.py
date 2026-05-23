"""Unit tests for envoy_local.cli_retry."""

import json
import sys
from unittest.mock import patch, mock_open
import pytest

from envoy_local.cli_retry import cmd_retry_validate, cmd_retry_show, register_retry_commands


def _make_args(**kwargs):
    class Args:
        pass
    a = Args()
    defaults = {"file": None, "json": "{}", "output": "text"}
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(a, k, v)
    return a


def test_cmd_retry_validate_valid_policy(capsys):
    args = _make_args(json=json.dumps({"retry_on": "5xx", "num_retries": 2}))
    cmd_retry_validate(args)
    out = capsys.readouterr().out
    assert "valid" in out.lower()


def test_cmd_retry_validate_invalid_policy_exits(capsys):
    args = _make_args(json=json.dumps({"retry_on": "bad-condition"}))
    with pytest.raises(SystemExit) as exc_info:
        cmd_retry_validate(args)
    assert exc_info.value.code == 2


def test_cmd_retry_validate_json_output(capsys):
    args = _make_args(
        json=json.dumps({"retry_on": "5xx"}),
        output="json",
    )
    cmd_retry_validate(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["valid"] is True
    assert data["errors"] == []


def test_cmd_retry_validate_file_not_found(capsys):
    args = _make_args(file="/nonexistent/policy.json")
    with pytest.raises(SystemExit) as exc_info:
        cmd_retry_validate(args)
    assert exc_info.value.code == 1


def test_cmd_retry_validate_invalid_json_exits(capsys):
    args = _make_args(json="not-json")
    with pytest.raises(SystemExit) as exc_info:
        cmd_retry_validate(args)
    assert exc_info.value.code == 1


def test_cmd_retry_show_prints_dict(capsys):
    args = _make_args(json=json.dumps({"retry_on": "5xx", "num_retries": 1}))
    cmd_retry_show(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["retry_on"] == "5xx"
    assert data["num_retries"] == 1


def test_cmd_retry_show_from_file(capsys, tmp_path):
    policy_file = tmp_path / "policy.json"
    policy_file.write_text(json.dumps({"retry_on": "reset", "num_retries": 5}))
    args = _make_args(file=str(policy_file))
    cmd_retry_show(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["retry_on"] == "reset"


def test_register_retry_commands_adds_subparsers():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_retry_commands(sub)
    args = parser.parse_args(["retry-validate", "--json", "{}"])
    assert hasattr(args, "func")
