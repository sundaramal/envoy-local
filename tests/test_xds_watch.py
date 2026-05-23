"""Tests for envoy_local.xds_watch."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest

from envoy_local.xds_watch import (
    fetch_xds_json,
    summarize_clusters,
    summarize_listeners,
    watch_xds,
    format_xds_summary,
)


CLUSTER_PAYLOAD = {
    "cluster_statuses": [
        {"name": "service_a"},
        {"name": "service_b"},
    ]
}

LISTENER_PAYLOAD = {
    "listener_statuses": [
        {"name": "listener_0"},
    ]
}


def _mock_urlopen(payload: dict):
    cm = MagicMock()
    cm.__enter__ = lambda s: s
    cm.__exit__ = MagicMock(return_value=False)
    cm.read.return_value = json.dumps(payload).encode()
    return cm


def test_fetch_xds_json_returns_dict():
    with patch("envoy_local.xds_watch.urlopen", return_value=_mock_urlopen(CLUSTER_PAYLOAD)):
        result = fetch_xds_json("http://localhost:9901", "/clusters?format=json")
    assert result == CLUSTER_PAYLOAD


def test_fetch_xds_json_raises_on_error():
    from urllib.error import URLError
    with patch("envoy_local.xds_watch.urlopen", side_effect=URLError("refused")):
        with pytest.raises(RuntimeError, match="Failed to fetch"):
            fetch_xds_json("http://localhost:9901", "/clusters?format=json")


def test_summarize_clusters_count_and_names():
    with patch("envoy_local.xds_watch.urlopen", return_value=_mock_urlopen(CLUSTER_PAYLOAD)):
        summary = summarize_clusters("http://localhost:9901")
    assert summary.count == 2
    assert "service_a" in summary.names
    assert "service_b" in summary.names
    assert summary.resource_type == "cluster"


def test_summarize_listeners_count_and_names():
    with patch("envoy_local.xds_watch.urlopen", return_value=_mock_urlopen(LISTENER_PAYLOAD)):
        summary = summarize_listeners("http://localhost:9901")
    assert summary.count == 1
    assert "listener_0" in summary.names
    assert summary.resource_type == "listener"


def test_summarize_clusters_empty_payload():
    with patch("envoy_local.xds_watch.urlopen", return_value=_mock_urlopen({})):
        summary = summarize_clusters("http://localhost:9901")
    assert summary.count == 0
    assert summary.names == []


def test_watch_xds_returns_both_types():
    def side_effect(url, timeout):
        if "clusters" in url:
            return _mock_urlopen(CLUSTER_PAYLOAD)
        return _mock_urlopen(LISTENER_PAYLOAD)

    with patch("envoy_local.xds_watch.urlopen", side_effect=side_effect):
        result = watch_xds("http://localhost:9901")

    assert "clusters" in result
    assert "listeners" in result
    assert result["clusters"].count == 2
    assert result["listeners"].count == 1


def test_format_xds_summary_contains_names():
    with patch("envoy_local.xds_watch.urlopen", side_effect=lambda url, timeout: (
        _mock_urlopen(CLUSTER_PAYLOAD) if "clusters" in url else _mock_urlopen(LISTENER_PAYLOAD)
    )):
        summaries = watch_xds("http://localhost:9901")
    text = format_xds_summary(summaries)
    assert "service_a" in text
    assert "listener_0" in text


def test_format_xds_summary_shows_none_when_empty():
    with patch("envoy_local.xds_watch.urlopen", return_value=_mock_urlopen({})):
        summaries = watch_xds("http://localhost:9901")
    text = format_xds_summary(summaries)
    assert "(none)" in text
