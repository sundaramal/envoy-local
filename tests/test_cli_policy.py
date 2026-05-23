"""Tests for envoy_local.cli_policy."""

import json
import sys
import pytest
from unittest.mock import patch, MagicMock

from envoy_local.cli_policy import cmd_policy_check, register_policy_commands
from envoy_local.network_policy import PolicyReport, PolicyViolation


def _make_args(config="config.yaml", policy="policy.json", as_json=False):
    args = MagicMock()
    args.config = config
    args.policy = policy
    args.json = as_json
    return args


@patch("envoy_local.cli_policy.evaluate_policy")
@patch("envoy_local.cli_policy._load_rules_from_file")
@patch("builtins.open")
@patch("envoy_local.cli_policy.yaml.safe_load")
def test_cmd_policy_check_compliant(mock_yaml, mock_open, mock_load_rules, mock_eval, capsys):
    mock_yaml.return_value = {"static_resources": {}}
    mock_load_rules.return_value = []
    mock_eval.return_value = PolicyReport(violations=[])

    cmd_policy_check(_make_args())
    out = capsys.readouterr().out
    assert "passed" in out


@patch("envoy_local.cli_policy.evaluate_policy")
@patch("envoy_local.cli_policy._load_rules_from_file")
@patch("builtins.open")
@patch("envoy_local.cli_policy.yaml.safe_load")
def test_cmd_policy_check_violations_printed(mock_yaml, mock_open, mock_load_rules, mock_eval, capsys):
    mock_yaml.return_value = {}
    mock_load_rules.return_value = []
    mock_eval.return_value = PolicyReport(
        violations=[PolicyViolation(rule_name="r1", message="bad port", severity="error")]
    )

    with pytest.raises(SystemExit) as exc:
        cmd_policy_check(_make_args())
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "bad port" in out
    assert "[ERROR]" in out


@patch("envoy_local.cli_policy.evaluate_policy")
@patch("envoy_local.cli_policy._load_rules_from_file")
@patch("builtins.open")
@patch("envoy_local.cli_policy.yaml.safe_load")
def test_cmd_policy_check_json_output(mock_yaml, mock_open, mock_load_rules, mock_eval, capsys):
    mock_yaml.return_value = {}
    mock_load_rules.return_value = []
    mock_eval.return_value = PolicyReport(
        violations=[PolicyViolation(rule_name="r1", message="msg", severity="warning")]
    )

    cmd_policy_check(_make_args(as_json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "violations" in data
    assert data["compliant"] is True  # warning only
    assert data["violations"][0]["rule"] == "r1"


def test_cmd_policy_check_config_not_found(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_policy_check(_make_args(config="/nonexistent/config.yaml"))
    assert exc.value.code == 1


@patch("builtins.open")
@patch("envoy_local.cli_policy.yaml.safe_load")
def test_cmd_policy_check_policy_not_found(mock_yaml, mock_open, capsys):
    mock_yaml.return_value = {}
    with patch("envoy_local.cli_policy._load_rules_from_file", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit) as exc:
            cmd_policy_check(_make_args())
    assert exc.value.code == 1


def test_register_policy_commands_adds_subparser():
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_policy_commands(subparsers)
    args = parser.parse_args(["policy-check", "cfg.yaml", "pol.json"])
    assert args.config == "cfg.yaml"
    assert args.policy == "pol.json"
