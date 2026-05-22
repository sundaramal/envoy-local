"""Tests for envoy_local.access_log_report."""

import pytest
from unittest.mock import patch

from envoy_local.access_log_report import generate_report, format_report


SAMPLE_ENTRIES = [
    {"path": "/api/v1", "status": 200, "duration_ms": 10.0},
    {"path": "/api/v1", "status": 200, "duration_ms": 20.0},
    {"path": "/health", "status": 200, "duration_ms": 5.0},
    {"path": "/api/v2", "status": 500, "duration_ms": 50.0},
    {"path": "/api/v2", "status": 502, "duration_ms": 30.0},
]


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_generate_report_total_requests(mock_parse):
    report = generate_report("/fake/path.log")
    assert report["total_requests"] == 5


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_generate_report_status_summary(mock_parse):
    report = generate_report("/fake/path.log")
    assert report["status_summary"][200] == 3
    assert report["status_summary"][500] == 1
    assert report["status_summary"][502] == 1


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_generate_report_average_duration(mock_parse):
    report = generate_report("/fake/path.log")
    expected_avg = (10.0 + 20.0 + 5.0 + 50.0 + 30.0) / 5
    assert report["average_duration_ms"] == pytest.approx(expected_avg)


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_generate_report_error_rate(mock_parse):
    report = generate_report("/fake/path.log")
    assert report["error_rate"] == pytest.approx(0.4)


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_generate_report_top_paths(mock_parse):
    report = generate_report("/fake/path.log")
    top = report["top_paths"]
    assert len(top) <= 5
    assert top[0]["path"] == "/api/v1"
    assert top[0]["count"] == 2


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=[])
def test_generate_report_empty_log(mock_parse):
    report = generate_report("/fake/empty.log")
    assert report["total_requests"] == 0
    assert report["status_summary"] == {}
    assert report["average_duration_ms"] is None
    assert report["error_rate"] == 0.0
    assert report["top_paths"] == []


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_format_report_contains_totals(mock_parse):
    report = generate_report("/fake/path.log")
    text = format_report(report)
    assert "Total Requests" in text
    assert "5" in text
    assert "Error Rate" in text
    assert "Top Paths" in text
    assert "/api/v1" in text


@patch("envoy_local.access_log_report.parse_access_log_file", return_value=SAMPLE_ENTRIES)
def test_format_report_error_rate_percentage(mock_parse):
    report = generate_report("/fake/path.log")
    text = format_report(report)
    assert "40.00%" in text
