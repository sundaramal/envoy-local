"""Tests for envoy_local.upstream_health."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest

from envoy_local.upstream_health import (
    fetch_clusters_json,
    parse_cluster_health,
    get_upstream_health,
    format_health_report,
    ClusterHealthReport,
    HostHealthStatus,
)


SAMPLE_RAW = {
    "cluster_statuses": [
        {
            "name": "backend",
            "host_statuses": [
                {
                    "address": {"socket_address": {"address": "10.0.0.1", "port_value": 8080}},
                    "health_status": {"eds_health_status": "HEALTHY"},
                    "weight": 1,
                },
                {
                    "address": {"socket_address": {"address": "10.0.0.2", "port_value": 8080}},
                    "health_status": {"eds_health_status": "UNHEALTHY"},
                    "weight": 1,
                },
            ],
        }
    ]
}


def _mock_urlopen(payload: dict):
    data = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = data
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch("envoy_local.upstream_health.urlopen", return_value=mock_resp)


def test_fetch_clusters_json_returns_dict():
    with _mock_urlopen(SAMPLE_RAW):
        result = fetch_clusters_json(9901)
    assert "cluster_statuses" in result


def test_fetch_clusters_json_raises_on_error():
    with patch("envoy_local.upstream_health.urlopen", side_effect=Exception("conn refused")):
        with pytest.raises(RuntimeError, match="Failed to fetch clusters"):
            fetch_clusters_json(9901)


def test_parse_cluster_health_counts_hosts():
    reports = parse_cluster_health(SAMPLE_RAW)
    assert len(reports) == 1
    r = reports[0]
    assert r.cluster_name == "backend"
    assert r.total_hosts == 2
    assert r.healthy_hosts == 1
    assert r.unhealthy_hosts == 1


def test_parse_cluster_health_percentage():
    reports = parse_cluster_health(SAMPLE_RAW)
    assert reports[0].health_percentage == 50.0


def test_parse_cluster_health_is_healthy_when_any_host_up():
    reports = parse_cluster_health(SAMPLE_RAW)
    assert reports[0].is_healthy is True


def test_parse_cluster_health_empty_returns_empty_list():
    assert parse_cluster_health({}) == []


def test_get_upstream_health_integration():
    with _mock_urlopen(SAMPLE_RAW):
        reports = get_upstream_health(9901)
    assert len(reports) == 1
    assert reports[0].cluster_name == "backend"


def test_format_health_report_healthy():
    report = ClusterHealthReport(cluster_name="svc", total_hosts=2, healthy_hosts=2)
    text = format_health_report([report])
    assert "HEALTHY" in text
    assert "svc" in text


def test_format_health_report_degraded():
    report = ClusterHealthReport(cluster_name="svc", total_hosts=2, healthy_hosts=0)
    text = format_health_report([report])
    assert "DEGRADED" in text


def test_format_health_report_empty():
    assert format_health_report([]) == "No clusters found."


def test_format_health_report_verbose_shows_hosts():
    h = HostHealthStatus(address="10.0.0.1", port=8080, healthy=True)
    report = ClusterHealthReport(cluster_name="svc", total_hosts=1, healthy_hosts=1, hosts=[h])
    text = format_health_report([report], verbose=True)
    assert "10.0.0.1" in text
    assert "UP" in text
