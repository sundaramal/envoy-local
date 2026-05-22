"""Tests for CLI command functions (start, stop, status)."""

from unittest.mock import patch

import pytest

from envoy_local.cli import cmd_start, cmd_status, cmd_stop
from envoy_local.config import EnvoyConfig


@pytest.fixture
def cfg():
    return EnvoyConfig(admin_port=9901)


def test_cmd_start_success(cfg):
    with patch("envoy_local.cli.get_running_pid", return_value=None), \
         patch("envoy_local.cli.EnvoyRunner") as MockRunner:
        MockRunner.return_value.start.return_value = 1234
        code = cmd_start(cfg)
    assert code == 0


def test_cmd_start_already_running(cfg):
    with patch("envoy_local.cli.get_running_pid", return_value=5678):
        code = cmd_start(cfg)
    assert code == 1


def test_cmd_start_binary_not_found(cfg):
    with patch("envoy_local.cli.get_running_pid", return_value=None), \
         patch("envoy_local.cli.EnvoyRunner") as MockRunner:
        MockRunner.return_value.start.side_effect = FileNotFoundError
        code = cmd_start(cfg)
    assert code == 2


def test_cmd_stop_success():
    with patch("envoy_local.cli.get_running_pid", return_value=42), \
         patch("envoy_local.cli.kill_process", return_value=True), \
         patch("envoy_local.cli.PID_FILE") as mock_pid:
        mock_pid.unlink = lambda missing_ok=False: None
        code = cmd_stop()
    assert code == 0


def test_cmd_stop_not_running():
    with patch("envoy_local.cli.get_running_pid", return_value=None):
        code = cmd_stop()
    assert code == 1


def test_cmd_status_running():
    with patch("envoy_local.cli.get_running_pid", return_value=99):
        code = cmd_status()
    assert code == 0


def test_cmd_status_not_running():
    with patch("envoy_local.cli.get_running_pid", return_value=None):
        code = cmd_status()
    assert code == 1
