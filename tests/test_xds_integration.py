"""Integration-style tests verifying xds_watch + cli_xds work end-to-end."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from envoy_local.xds_watch import XdsResourceSummary, format_xds_summary
from envoy_local.cli_xds import register_xds_commands

import argparse


SAMPLE_SUMMARIES = {
    "clusters": XdsResourceSummary(resource_type="cluster", names=["backend"], count=1),
    "listeners": XdsResourceSummary(resource_type="listener", names=[], count=0),
}


def test_format_summary_empty_listeners_shows_none():
    text = format_xds_summary(SAMPLE_SUMMARIES)
    assert "(none)" in text
    assert "backend" in text


def test_register_xds_commands_adds_subparsers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_xds_commands(subparsers)
    args = parser.parse_args(["xds-watch", "--admin-url", "http://localhost:9901"])
    assert hasattr(args, "func")
    assert args.admin_url == "http://localhost:9901"


def test_register_xds_clusters_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_xds_commands(subparsers)
    args = parser.parse_args(["xds-clusters", "--json"])
    assert hasattr(args, "func")
    assert args.json is True


def test_xds_watch_full_flow_text(capsys):
    with patch("envoy_local.cli_xds.watch_xds", return_value=SAMPLE_SUMMARIES):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_xds_commands(subparsers)
        args = parser.parse_args(["xds-watch"])
        args.func(args)
    out = capsys.readouterr().out
    assert "backend" in out


def test_xds_watch_full_flow_json(capsys):
    with patch("envoy_local.cli_xds.watch_xds", return_value=SAMPLE_SUMMARIES):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_xds_commands(subparsers)
        args = parser.parse_args(["xds-watch", "--json"])
        args.func(args)
    data = json.loads(capsys.readouterr().out)
    assert "clusters" in data
    assert "listeners" in data
    assert data["listeners"]["count"] == 0
