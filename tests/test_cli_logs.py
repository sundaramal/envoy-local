"""Tests for envoy_local.cli_logs commands."""

import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from envoy_local.cli_logs import (
    cmd_logs_tail,
    cmd_logs_filter,
    cmd_logs_clear,
    cmd_logs_path,
)


SAMPLE_LINES = ["[info] started", "[error] failed", "[info] retrying"]


@pytest.fixture
def args(tmp_path):
    return SimpleNamespace(log_dir=str(tmp_path), lines=50, level="info")


def test_cmd_logs_tail_success(args, capsys):
    with patch("envoy_local.cli_logs.tail_log", return_value=SAMPLE_LINES):
        code = cmd_logs_tail(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "[info] started" in captured.out


def test_cmd_logs_tail_file_not_found(args, capsys):
    with patch("envoy_local.cli_logs.tail_log", side_effect=FileNotFoundError("missing")):
        code = cmd_logs_tail(args)
    assert code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_cmd_logs_filter_success(args, capsys):
    with patch("envoy_local.cli_logs.filter_log_by_level", return_value=["[info] started"]):
        code = cmd_logs_filter(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "[info] started" in captured.out


def test_cmd_logs_filter_no_matches(args, capsys):
    with patch("envoy_local.cli_logs.filter_log_by_level", return_value=[]):
        code = cmd_logs_filter(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "No log entries" in captured.out


def test_cmd_logs_filter_file_not_found(args, capsys):
    with patch(
        "envoy_local.cli_logs.filter_log_by_level",
        side_effect=FileNotFoundError("no file"),
    ):
        code = cmd_logs_filter(args)
    assert code == 1


def test_cmd_logs_clear_success(args, capsys):
    with patch("envoy_local.cli_logs.clear_log") as mock_clear:
        code = cmd_logs_clear(args)
    assert code == 0
    mock_clear.assert_called_once()
    captured = capsys.readouterr()
    assert "cleared" in captured.out


def test_cmd_logs_clear_file_not_found(args, capsys):
    with patch("envoy_local.cli_logs.clear_log", side_effect=FileNotFoundError("gone")):
        code = cmd_logs_clear(args)
    assert code == 1


def test_cmd_logs_path_prints_path(args, capsys):
    code = cmd_logs_path(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "envoy.log" in captured.out
