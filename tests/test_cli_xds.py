"""Tests for envoy_local.cli_xds."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from envoy_local.xds_watch import XdsResourceSummary
from envoy_local.cli_xds import cmd_xds_watch, cmd_xds_clusters


def _make_args(**kwargs):
    defaults = {"admin_url": "http://localhost:9901", "json": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


SAMPLE_SUMMARIES = {
    "clusters": XdsResourceSummary(resource_type="cluster", names=["svc_a"], count=1),
    "listeners": XdsResourceSummary(resource_type="listener", names=["l0"], count=1),
}


def test_cmd_xds_watch_prints_text(capsys):
    with patch("envoy_local.cli_xds.watch_xds", return_value=SAMPLE_SUMMARIES):
        cmd_xds_watch(_make_args())
    out = capsys.readouterr().out
    assert "svc_a" in out
    assert "l0" in out


def test_cmd_xds_watch_json_output(capsys):
    with patch("envoy_local.cli_xds.watch_xds", return_value=SAMPLE_SUMMARIES):
        cmd_xds_watch(_make_args(json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["clusters"]["count"] == 1
    assert "svc_a" in data["clusters"]["names"]


def test_cmd_xds_watch_error_exits(capsys):
    with patch("envoy_local.cli_xds.watch_xds", side_effect=RuntimeError("conn refused")):
        with pytest.raises(SystemExit) as exc_info:
            cmd_xds_watch(_make_args())
    assert exc_info.value.code == 1
    assert "conn refused" in capsys.readouterr().err


def test_cmd_xds_clusters_prints_names(capsys):
    summary = XdsResourceSummary(resource_type="cluster", names=["svc_x", "svc_y"], count=2)
    with patch("envoy_local.cli_xds.summarize_clusters", return_value=summary):
        cmd_xds_clusters(_make_args())
    out = capsys.readouterr().out
    assert "svc_x" in out
    assert "svc_y" in out


def test_cmd_xds_clusters_json_output(capsys):
    summary = XdsResourceSummary(resource_type="cluster", names=["svc_x"], count=1)
    with patch("envoy_local.cli_xds.summarize_clusters", return_value=summary):
        cmd_xds_clusters(_make_args(json=True))
    data = json.loads(capsys.readouterr().out)
    assert data["count"] == 1
    assert "svc_x" in data["names"]


def test_cmd_xds_clusters_error_exits(capsys):
    with patch("envoy_local.cli_xds.summarize_clusters", side_effect=RuntimeError("timeout")):
        with pytest.raises(SystemExit) as exc_info:
            cmd_xds_clusters(_make_args())
    assert exc_info.value.code == 1
