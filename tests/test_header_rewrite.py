"""Tests for header_rewrite module and cli_header_rewrite commands."""
from __future__ import annotations

import json
import sys
import types
from unittest.mock import patch

import pytest

from envoy_local.header_rewrite import (
    HeaderRewriteRule,
    rules_to_envoy_headers,
    validate_rule,
    validate_rules,
)
from envoy_local.cli_header_rewrite import cmd_header_validate, cmd_header_show


# ---------------------------------------------------------------------------
# validate_rule
# ---------------------------------------------------------------------------

def test_valid_add_rule():
    rule = HeaderRewriteRule(action="add", header="X-Custom", value="hello")
    result = validate_rule(rule)
    assert result.is_valid
    assert result.errors == []
    assert result.warnings == []


def test_valid_remove_rule():
    rule = HeaderRewriteRule(action="remove", header="X-Remove")
    result = validate_rule(rule)
    assert result.is_valid


def test_remove_with_value_produces_warning():
    rule = HeaderRewriteRule(action="remove", header="X-Remove", value="oops")
    result = validate_rule(rule)
    assert result.is_valid
    assert any("ignored" in w for w in result.warnings)


def test_invalid_action_produces_error():
    rule = HeaderRewriteRule(action="replace", header="X-H", value="v")
    result = validate_rule(rule)
    assert not result.is_valid
    assert any("Invalid action" in e for e in result.errors)


def test_empty_header_name_is_error():
    rule = HeaderRewriteRule(action="add", header="", value="v")
    result = validate_rule(rule)
    assert not result.is_valid


def test_add_without_value_is_error():
    rule = HeaderRewriteRule(action="add", header="X-H", value=None)
    result = validate_rule(rule)
    assert not result.is_valid


# ---------------------------------------------------------------------------
# validate_rules
# ---------------------------------------------------------------------------

def test_duplicate_header_produces_warning():
    rules = [
        HeaderRewriteRule(action="add", header="X-H", value="a"),
        HeaderRewriteRule(action="override", header="x-h", value="b"),
    ]
    result = validate_rules(rules)
    assert result.is_valid
    assert any("multiple rules" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# rules_to_envoy_headers
# ---------------------------------------------------------------------------

def test_rules_to_envoy_headers_add():
    rules = [HeaderRewriteRule(action="add", header="X-Foo", value="bar")]
    out = rules_to_envoy_headers(rules)
    assert "request_headers_to_add" in out
    assert out["request_headers_to_add"][0]["header"]["key"] == "X-Foo"


def test_rules_to_envoy_headers_remove():
    rules = [HeaderRewriteRule(action="remove", header="X-Del")]
    out = rules_to_envoy_headers(rules)
    assert "request_headers_to_remove" in out
    assert "X-Del" in out["request_headers_to_remove"]


def test_rules_to_envoy_headers_empty():
    assert rules_to_envoy_headers([]) == {}


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    args = types.SimpleNamespace(json=False)
    args.__dict__.update(kwargs)
    return args


def test_cmd_header_validate_valid(capsys):
    args = _make_args(rules=["add:X-Req:1", "remove:X-Old"])
    cmd_header_validate(args)
    out = capsys.readouterr().out
    assert "valid" in out.lower()


def test_cmd_header_validate_invalid_exits(capsys):
    args = _make_args(rules=["add:X-H"])  # missing value
    with pytest.raises(SystemExit):
        cmd_header_validate(args)


def test_cmd_header_validate_json_output(capsys):
    args = _make_args(rules=["add:X-H:val"], json=True)
    cmd_header_validate(args)
    data = json.loads(capsys.readouterr().out)
    assert data["valid"] is True


def test_cmd_header_show_outputs_json(capsys):
    args = _make_args(rules=["add:X-Foo:bar", "remove:X-Old"])
    cmd_header_show(args)
    data = json.loads(capsys.readouterr().out)
    assert "request_headers_to_add" in data
    assert "request_headers_to_remove" in data
