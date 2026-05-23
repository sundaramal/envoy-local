"""Integration-style tests for upstream health flow."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

from envoy_local.upstream_health import (
    get_upstream_health,
    format_health_report,
)


def _make_urlopen(payload: dict):
    data = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = data
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch("envoy_local.upstream_health.urlopen", return_value=mock_resp)


MULTI_CLUSTER_RAW = {
    "cluster_statuses": [
        {
            "name": "alpha",
            "host_statuses": [
                {
                    "address": {"socket_address": {"address": "1.1.1.1", "port_value": 80}},
                    "health_status": {"eds_health_status": "HEALTHY"},
                    "weight": 2,
                }
            ],
        },
        {
            "name": "beta",
            "host_statuses": [
                {
                    "address": {"socket_address": {"address": "2.2.2.2", "port_value": 80}},
                    "health_status": {"eds_health_status": "UNHEALTHY"},
                    "weight": 1,
                }
            ],
        },
    ]
}


def test_full_flow_multi_cluster_text():
    with _make_urlopen(MULTI_CLUSTER_RAW):
        reports = get_upstream_health(9901)
    text = format_health_report(reports)
    assert "alpha" in text
    assert "beta" in text
    assert "HEALTHY" in text
    assert "DEGRADED" in text


def test_full_flow_all_healthy_cluster():
    with _make_urlopen(MULTI_CLUSTER_RAW):
        reports = get_upstream_health(9901)
    alpha = next(r for r in reports if r.cluster_name == "alpha")
    assert alpha.is_healthy is True
    assert alpha.health_percentage == 100.0


def test_full_flow_all_unhealthy_cluster():
    with _make_urlopen(MULTI_CLUSTER_RAW):
        reports = get_upstream_health(9901)
    beta = next(r for r in reports if r.cluster_name == "beta")
    assert beta.is_healthy is False
    assert beta.health_percentage == 0.0


def test_full_flow_verbose_includes_addresses():
    with _make_urlopen(MULTI_CLUSTER_RAW):
        reports = get_upstream_health(9901)
    text = format_health_report(reports, verbose=True)
    assert "1.1.1.1" in text
    assert "2.2.2.2" in text


def test_full_flow_empty_cluster_statuses():
    with _make_urlopen({"cluster_statuses": []}):
        reports = get_upstream_health(9901)
    assert reports == []
    assert format_health_report(reports) == "No clusters found."
