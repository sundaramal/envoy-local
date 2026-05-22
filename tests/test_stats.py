"""Tests for envoy_local.stats module."""

import pytest
from unittest.mock import patch, MagicMock
from envoy_local.stats import fetch_stats_text, parse_stats, get_stats, filter_stats


SAMPLE_STATS = (
    "cluster.local_service.upstream_cx_total: 42\n"
    "cluster.local_service.upstream_rq_total: 100\n"
    "http.admin.downstream_cx_total: 5\n"
    "server.uptime: 3600\n"
)

ADMIN_PORT = 9901


def _mock_urlopen(text: str):
    mock_resp = MagicMock()
    mock_resp.read.return_value = text.encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_fetch_stats_text_success():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(SAMPLE_STATS)):
        result = fetch_stats_text(ADMIN_PORT)
    assert result == SAMPLE_STATS


def test_fetch_stats_text_failure():
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
        result = fetch_stats_text(ADMIN_PORT)
    assert result is None


def test_parse_stats_returns_dict():
    parsed = parse_stats(SAMPLE_STATS)
    assert parsed["cluster.local_service.upstream_cx_total"] == "42"
    assert parsed["server.uptime"] == "3600"


def test_parse_stats_skips_invalid_lines():
    raw = "valid.key: 1\nno_colon_here\n\n"
    parsed = parse_stats(raw)
    assert "valid.key" in parsed
    assert len(parsed) == 1


def test_get_stats_returns_dict_on_success():
    with patch("envoy_local.stats.fetch_stats_text", return_value=SAMPLE_STATS):
        result = get_stats(ADMIN_PORT)
    assert isinstance(result, dict)
    assert "server.uptime" in result


def test_get_stats_returns_none_when_unreachable():
    with patch("envoy_local.stats.fetch_stats_text", return_value=None):
        result = get_stats(ADMIN_PORT)
    assert result is None


def test_filter_stats_by_prefix():
    parsed = parse_stats(SAMPLE_STATS)
    cluster_stats = filter_stats(parsed, "cluster.")
    assert all(k.startswith("cluster.") for k in cluster_stats)
    assert "server.uptime" not in cluster_stats


def test_filter_stats_empty_when_no_match():
    parsed = parse_stats(SAMPLE_STATS)
    result = filter_stats(parsed, "nonexistent.prefix")
    assert result == {}
