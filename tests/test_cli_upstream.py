"""Tests for envoy_local.cli_upstream."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from unittest.mock import patch

import pytest

from envoy_local.cli_upstream import (
    cmd_upstream_health,
    cmd_upstream_summary,
    register_upstream_commands,
)
from envoy_local.upstream_health import ClusterHealthReport, HostHealthStatus


def _make_args(**kwargs):
    defaults = {"admin_port": 9901, "json": False, "verbose": False}
    defaults.update(kwargs)
    return Namespace(**defaults)


SAMPLE_REPORTS = [
    ClusterHealthReport(
        cluster_name="backend",
        total_hosts=2,
        healthy_hosts=1,
        unhealthy_hosts=1,
        hosts=[
            HostHealthStatus(address="10.0.0.1", port=8080, healthy=True),
            HostHealthStatus(address="10.0.0.2", port=8080, healthy=False),
        ],
    )
]


def test_cmd_upstream_health_prints_text(capsys):
    with patch("envoy_local.cli_upstream.get_upstream_health", return_value=SAMPLE_REPORTS):
        cmd_upstream_health(_make_args())
    out = capsys.readouterr().out
    assert "backend" in out


def test_cmd_upstream_health_json_output(capsys):
    with patch("envoy_local.cli_upstream.get_upstream_health", return_value=SAMPLE_REPORTS):
        cmd_upstream_health(_make_args(json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data[0]["cluster"] == "backend"
    assert data[0]["total_hosts"] == 2


def test_cmd_upstream_health_error_exits(capsys):
    with patch("envoy_local.cli_upstream.get_upstream_health", side_effect=RuntimeError("down")):
        with pytest.raises(SystemExit) as exc:
            cmd_upstream_health(_make_args())
    assert exc.value.code == 1
    assert "down" in capsys.readouterr().err


def test_cmd_upstream_summary_prints_line(capsys):
    with patch("envoy_local.cli_upstream.get_upstream_health", return_value=SAMPLE_REPORTS):
        cmd_upstream_summary(_make_args())
    out = capsys.readouterr().out
    assert "1/1" in out
    assert "healthy" in out


def test_cmd_upstream_summary_error_exits(capsys):
    with patch("envoy_local.cli_upstream.get_upstream_health", side_effect=RuntimeError("err")):
        with pytest.raises(SystemExit):
            cmd_upstream_summary(_make_args())


def test_register_upstream_commands_adds_subparsers():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_upstream_commands(sub)
    args = parser.parse_args(["upstream-health", "--admin-port", "9902"])
    assert args.admin_port == 9902
    assert args.func is cmd_upstream_health


def test_register_upstream_summary_subcommand():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_upstream_commands(sub)
    args = parser.parse_args(["upstream-summary"])
    assert args.func is cmd_upstream_summary
