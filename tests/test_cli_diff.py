"""Tests for envoy_local.cli_diff module."""

import json
import os
import types
import pytest

from unittest.mock import patch, MagicMock
from envoy_local.cli_diff import cmd_diff_snapshots, cmd_diff_files
from envoy_local.diff import DiffResult


OLD = {"admin": {"port": 9901}}
NEW = {"admin": {"port": 9902}}


def _args(**kwargs):
    base = types.SimpleNamespace(json=False, snapshots_dir=None)
    for k, v in kwargs.items():
        setattr(base, k, v)
    return base


@patch("envoy_local.cli_diff.load_snapshot")
def test_cmd_diff_snapshots_no_changes(mock_load, capsys):
    mock_load.side_effect = [OLD, OLD]
    args = _args(snapshot_a="snap1", snapshot_b="snap2")
    rc = cmd_diff_snapshots(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No differences" in out


@patch("envoy_local.cli_diff.load_snapshot")
def test_cmd_diff_snapshots_with_changes(mock_load, capsys):
    mock_load.side_effect = [OLD, NEW]
    args = _args(snapshot_a="snap1", snapshot_b="snap2")
    rc = cmd_diff_snapshots(args)
    assert rc == 2
    out = capsys.readouterr().out
    assert "admin.port" in out


@patch("envoy_local.cli_diff.load_snapshot")
def test_cmd_diff_snapshots_file_not_found(mock_load, capsys):
    mock_load.side_effect = FileNotFoundError("snap1 not found")
    args = _args(snapshot_a="snap1", snapshot_b="snap2")
    rc = cmd_diff_snapshots(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


@patch("envoy_local.cli_diff.load_snapshot")
def test_cmd_diff_snapshots_json_output(mock_load, capsys):
    mock_load.side_effect = [OLD, NEW]
    args = _args(snapshot_a="snap1", snapshot_b="snap2", json=True)
    rc = cmd_diff_snapshots(args)
    assert rc == 2
    data = json.loads(capsys.readouterr().out)
    assert "changed" in data


def test_cmd_diff_files_no_changes(tmp_path, capsys):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps(OLD))
    b.write_text(json.dumps(OLD))
    args = _args(file_a=str(a), file_b=str(b))
    rc = cmd_diff_files(args)
    assert rc == 0


def test_cmd_diff_files_with_changes(tmp_path, capsys):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps(OLD))
    b.write_text(json.dumps(NEW))
    args = _args(file_a=str(a), file_b=str(b))
    rc = cmd_diff_files(args)
    assert rc == 2


def test_cmd_diff_files_missing_file(tmp_path, capsys):
    args = _args(file_a="/nonexistent/a.json", file_b="/nonexistent/b.json")
    rc = cmd_diff_files(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err
