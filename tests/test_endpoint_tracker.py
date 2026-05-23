"""Tests for envoy_local.endpoint_tracker."""

import json
import sys
import types
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from envoy_local.endpoint_tracker import (
    EndpointDiff,
    EndpointSnapshot,
    diff_snapshots,
    format_diff,
    parse_endpoints_from_clusters,
)


# ---------------------------------------------------------------------------
# EndpointSnapshot
# ---------------------------------------------------------------------------

def test_snapshot_to_dict_round_trip():
    snap = EndpointSnapshot(cluster="svc", addresses=["1.2.3.4:80"], timestamp=1.0)
    d = snap.to_dict()
    restored = EndpointSnapshot.from_dict(d)
    assert restored.cluster == "svc"
    assert restored.addresses == ["1.2.3.4:80"]
    assert restored.timestamp == 1.0


def test_snapshot_from_dict_missing_timestamp_defaults_zero():
    snap = EndpointSnapshot.from_dict({"cluster": "x", "addresses": []})
    assert snap.timestamp == 0.0


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_no_changes():
    before = EndpointSnapshot("svc", ["1.0.0.1:80", "1.0.0.2:80"])
    after = EndpointSnapshot("svc", ["1.0.0.1:80", "1.0.0.2:80"])
    diff = diff_snapshots(before, after)
    assert not diff.has_changes
    assert diff.added == []
    assert diff.removed == []


def test_diff_detects_added_address():
    before = EndpointSnapshot("svc", ["1.0.0.1:80"])
    after = EndpointSnapshot("svc", ["1.0.0.1:80", "1.0.0.2:80"])
    diff = diff_snapshots(before, after)
    assert diff.added == ["1.0.0.2:80"]
    assert diff.removed == []
    assert diff.has_changes


def test_diff_detects_removed_address():
    before = EndpointSnapshot("svc", ["1.0.0.1:80", "1.0.0.2:80"])
    after = EndpointSnapshot("svc", ["1.0.0.1:80"])
    diff = diff_snapshots(before, after)
    assert diff.removed == ["1.0.0.2:80"]
    assert diff.added == []


# ---------------------------------------------------------------------------
# parse_endpoints_from_clusters
# ---------------------------------------------------------------------------

SAMPLE_CLUSTERS_JSON = {
    "cluster_statuses": [
        {
            "name": "backend",
            "host_statuses": [
                {"address": {"socket_address": {"address": "10.0.0.1", "port_value": 8080}}},
                {"address": {"socket_address": {"address": "10.0.0.2", "port_value": 8080}}},
            ],
        },
        {
            "name": "empty_cluster",
            "host_statuses": [],
        },
    ]
}


def test_parse_endpoints_returns_snapshots():
    snaps = parse_endpoints_from_clusters(SAMPLE_CLUSTERS_JSON)
    assert len(snaps) == 2
    backend = next(s for s in snaps if s.cluster == "backend")
    assert "10.0.0.1:8080" in backend.addresses
    assert "10.0.0.2:8080" in backend.addresses


def test_parse_endpoints_empty_cluster_has_no_addresses():
    snaps = parse_endpoints_from_clusters(SAMPLE_CLUSTERS_JSON)
    empty = next(s for s in snaps if s.cluster == "empty_cluster")
    assert empty.addresses == []


def test_parse_endpoints_empty_payload():
    snaps = parse_endpoints_from_clusters({})
    assert snaps == []


# ---------------------------------------------------------------------------
# format_diff
# ---------------------------------------------------------------------------

def test_format_diff_no_changes():
    diff = EndpointDiff(cluster="svc", added=[], removed=[])
    assert "no endpoint changes" in format_diff(diff)


def test_format_diff_shows_added_and_removed():
    diff = EndpointDiff(cluster="svc", added=["1.0.0.3:80"], removed=["1.0.0.1:80"])
    text = format_diff(diff)
    assert "+ 1.0.0.3:80" in text
    assert "- 1.0.0.1:80" in text
