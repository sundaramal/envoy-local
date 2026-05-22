"""Tests for envoy_local.logs module."""

import os
import pytest
from unittest.mock import patch, mock_open

from envoy_local.logs import (
    get_log_path,
    tail_log,
    filter_log_by_level,
    clear_log,
    iter_log_lines,
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_FILE,
)


SAMPLE_LOG = """[2024-01-01 00:00:01][info] upstream connected
[2024-01-01 00:00:02][debug] request received
[2024-01-01 00:00:03][error] connection reset
[2024-01-01 00:00:04][warning] retry limit reached
[2024-01-01 00:00:05][info] response sent
"""


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "envoy.log"
    p.write_text(SAMPLE_LOG)
    return str(p)


def test_get_log_path_returns_string(tmp_path):
    path = get_log_path(log_dir=str(tmp_path))
    assert path.endswith(DEFAULT_LOG_FILE)
    assert str(tmp_path) in path


def test_get_log_path_creates_directory(tmp_path):
    new_dir = str(tmp_path / "nested" / "logs")
    path = get_log_path(log_dir=new_dir)
    assert os.path.isdir(new_dir)


def test_tail_log_returns_last_n_lines(log_file):
    lines = tail_log(log_file, lines=2)
    assert len(lines) == 2
    assert "response sent" in lines[-1]


def test_tail_log_all_lines_when_fewer_than_n(log_file):
    lines = tail_log(log_file, lines=100)
    assert len(lines) == 5


def test_tail_log_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        tail_log("/nonexistent/path/envoy.log")


def test_filter_log_by_level_info(log_file):
    lines = filter_log_by_level(log_file, "info")
    assert len(lines) == 2
    assert all("[info]" in l for l in lines)


def test_filter_log_by_level_error(log_file):
    lines = filter_log_by_level(log_file, "error")
    assert len(lines) == 1
    assert "connection reset" in lines[0]


def test_filter_log_by_level_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        filter_log_by_level("/no/such/file.log", "debug")


def test_clear_log_truncates_file(log_file):
    clear_log(log_file)
    assert os.path.getsize(log_file) == 0


def test_clear_log_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        clear_log("/no/such/file.log")


def test_iter_log_lines_yields_all(log_file):
    result = list(iter_log_lines(log_file))
    assert len(result) == 5
    assert result[0].startswith("[2024")
