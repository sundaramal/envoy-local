"""Tests for envoy_local.port_scanner."""

import socket
from unittest.mock import MagicMock, patch

import pytest

from envoy_local.port_scanner import (
    PortScanResult,
    ScanReport,
    format_scan_report,
    probe_port,
    scan_config_ports,
)


def test_probe_port_open():
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=None)
    mock_cm.__exit__ = MagicMock(return_value=False)
    with patch("envoy_local.port_scanner.socket.create_connection", return_value=mock_cm):
        result = probe_port("127.0.0.1", 9901, label="admin")
    assert result.is_open is True
    assert result.port == 9901
    assert result.label == "admin"
    assert result.error is None


def test_probe_port_closed():
    with patch(
        "envoy_local.port_scanner.socket.create_connection",
        side_effect=ConnectionRefusedError("refused"),
    ):
        result = probe_port("127.0.0.1", 9901)
    assert result.is_open is False
    assert result.error is not None


def test_probe_port_os_error():
    with patch(
        "envoy_local.port_scanner.socket.create_connection",
        side_effect=OSError("network unreachable"),
    ):
        result = probe_port("127.0.0.1", 8080)
    assert result.is_open is False
    assert "network unreachable" in result.error


@pytest.fixture
def sample_config():
    return {
        "admin": {"address": {"socket_address": {"port_value": 9901}}},
        "static_resources": {
            "listeners": [
                {
                    "name": "ingress",
                    "address": {"socket_address": {"port_value": 10000}},
                }
            ]
        },
    }


def test_scan_config_ports_probes_admin_and_listeners(sample_config):
    with patch("envoy_local.port_scanner.probe_port") as mock_probe:
        mock_probe.side_effect = lambda host, port, timeout, label: PortScanResult(
            port=port, host=host, is_open=True, label=label
        )
        report = scan_config_ports(sample_config)
    assert len(report.results) == 2
    labels = {r.label for r in report.results}
    assert "admin" in labels
    assert "ingress" in labels


def test_scan_config_ports_empty_config():
    report = scan_config_ports({})
    assert report.results == []


def test_scan_report_open_closed_split():
    report = ScanReport(
        results=[
            PortScanResult(port=9901, host="127.0.0.1", is_open=True),
            PortScanResult(port=8080, host="127.0.0.1", is_open=False),
        ]
    )
    assert len(report.open_ports) == 1
    assert len(report.closed_ports) == 1


def test_format_scan_report_contains_status():
    report = ScanReport(
        results=[
            PortScanResult(port=9901, host="127.0.0.1", is_open=True, label="admin"),
            PortScanResult(port=8080, host="127.0.0.1", is_open=False, error="refused"),
        ]
    )
    output = format_scan_report(report)
    assert "OPEN" in output
    assert "CLOSED" in output
    assert "1/2 port(s) open." in output
