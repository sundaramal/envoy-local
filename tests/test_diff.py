"""Tests for envoy_local.diff module."""

import pytest
from envoy_local.diff import DiffResult, diff_configs, format_diff


OLD_CONFIG = {
    "admin": {"port": 9901},
    "clusters": [{"name": "backend", "endpoints": ["127.0.0.1:8080"]}],
    "listeners": [{"port": 10000}],
}

NEW_CONFIG = {
    "admin": {"port": 9902},
    "clusters": [
        {"name": "backend", "endpoints": ["127.0.0.1:8080"]},
        {"name": "cache", "endpoints": ["127.0.0.1:6379"]},
    ],
    "listeners": [{"port": 10000}],
}


def test_diff_detects_changed_value():
    result = diff_configs(OLD_CONFIG, NEW_CONFIG)
    changed_keys = [k for k, _, _ in result.changed]
    assert "admin.port" in changed_keys


def test_diff_detects_added_key():
    result = diff_configs(OLD_CONFIG, NEW_CONFIG)
    assert any("cache" in k for k in result.added)


def test_diff_no_changes_when_equal():
    result = diff_configs(OLD_CONFIG, OLD_CONFIG)
    assert not result.has_changes


def test_diff_detects_removed_key():
    result = diff_configs(NEW_CONFIG, OLD_CONFIG)
    assert any("cache" in k for k in result.removed)


def test_has_changes_true_when_changed():
    result = DiffResult(changed=[("admin.port", 9901, 9902)])
    assert result.has_changes


def test_has_changes_false_when_empty():
    result = DiffResult()
    assert not result.has_changes


def test_format_diff_no_changes():
    result = DiffResult()
    assert format_diff(result) == "No differences found."


def test_format_diff_shows_added():
    result = DiffResult(added=["clusters[1].name"])
    output = format_diff(result)
    assert "+ clusters[1].name" in output


def test_format_diff_shows_removed():
    result = DiffResult(removed=["clusters[1].name"])
    output = format_diff(result)
    assert "- clusters[1].name" in output


def test_format_diff_shows_changed():
    result = DiffResult(changed=[("admin.port", 9901, 9902)])
    output = format_diff(result)
    assert "~ admin.port" in output
    assert "9901" in output
    assert "9902" in output


def test_diff_identical_nested_lists():
    cfg = {"routes": [{"match": "/a", "cluster": "svc"}]}
    result = diff_configs(cfg, cfg)
    assert not result.has_changes
