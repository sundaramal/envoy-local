"""Tests for the EnvoyRunner process lifecycle management."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envoy_local.config import EnvoyConfig
from envoy_local.runner import EnvoyRunner, PID_FILE


@pytest.fixture
def basic_config():
    return EnvoyConfig(admin_port=9901)


@pytest.fixture(autouse=True)
def cleanup_pid_file():
    yield
    if PID_FILE.exists():
        PID_FILE.unlink()


def test_start_writes_pid_file(basic_config, tmp_path):
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.pid = 12345
    mock_proc.poll.return_value = None

    with patch("envoy_local.runner.subprocess.Popen", return_value=mock_proc):
        runner = EnvoyRunner(basic_config)
        pid = runner.start()

    assert pid == 12345
    assert PID_FILE.exists()
    assert PID_FILE.read_text() == "12345"


def test_start_raises_if_already_running(basic_config):
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.pid = 99
    mock_proc.poll.return_value = None

    with patch("envoy_local.runner.subprocess.Popen", return_value=mock_proc):
        runner = EnvoyRunner(basic_config)
        runner.start()
        with pytest.raises(RuntimeError, match="already running"):
            runner.start()


def test_stop_terminates_process(basic_config):
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.pid = 42
    mock_proc.poll.return_value = None

    with patch("envoy_local.runner.subprocess.Popen", return_value=mock_proc):
        runner = EnvoyRunner(basic_config)
        runner.start()
        runner.stop()

    mock_proc.send_signal.assert_called_once()
    assert not runner.is_running()


def test_stop_raises_if_not_running(basic_config):
    runner = EnvoyRunner(basic_config)
    with pytest.raises(RuntimeError, match="No Envoy process"):
        runner.stop()


def test_is_running_false_when_process_exits(basic_config):
    mock_proc = MagicMock(spec=subprocess.Popen)
    mock_proc.pid = 7
    mock_proc.poll.side_effect = [None, 0]

    with patch("envoy_local.runner.subprocess.Popen", return_value=mock_proc):
        runner = EnvoyRunner(basic_config)
        runner.start()
        assert runner.is_running() is True
        assert runner.is_running() is False
