"""Tests for envoy_local.snapshot."""

import json
import os
import pytest

from envoy_local.snapshot import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
)


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path / "snapshots")


SAMPLE_CONFIG = {"admin": {"port": 9901}, "clusters": [], "listeners": []}


def test_save_snapshot_creates_file(snap_dir):
    path = save_snapshot(SAMPLE_CONFIG, name="test-snap", directory=snap_dir)
    assert os.path.isfile(path)
    assert path.endswith("test-snap.json")


def test_save_snapshot_content_is_valid_json(snap_dir):
    path = save_snapshot(SAMPLE_CONFIG, name="content-test", directory=snap_dir)
    with open(path) as fh:
        data = json.load(fh)
    assert data == SAMPLE_CONFIG


def test_save_snapshot_auto_name(snap_dir):
    path = save_snapshot(SAMPLE_CONFIG, directory=snap_dir)
    assert os.path.isfile(path)
    # auto-generated name follows timestamp pattern
    basename = os.path.basename(path)
    assert basename.endswith(".json")
    assert len(basename) > 5


def test_load_snapshot_returns_dict(snap_dir):
    save_snapshot(SAMPLE_CONFIG, name="load-test", directory=snap_dir)
    result = load_snapshot("load-test", directory=snap_dir)
    assert result == SAMPLE_CONFIG


def test_load_snapshot_missing_raises(snap_dir):
    with pytest.raises(FileNotFoundError):
        load_snapshot("nonexistent", directory=snap_dir)


def test_list_snapshots_empty_dir(snap_dir):
    assert list_snapshots(snap_dir) == []


def test_list_snapshots_nonexistent_dir(tmp_path):
    assert list_snapshots(str(tmp_path / "no-such-dir")) == []


def test_list_snapshots_returns_names(snap_dir):
    save_snapshot(SAMPLE_CONFIG, name="alpha", directory=snap_dir)
    save_snapshot(SAMPLE_CONFIG, name="beta", directory=snap_dir)
    names = list_snapshots(snap_dir)
    assert set(names) == {"alpha", "beta"}


def test_delete_snapshot_removes_file(snap_dir):
    save_snapshot(SAMPLE_CONFIG, name="to-delete", directory=snap_dir)
    result = delete_snapshot("to-delete", directory=snap_dir)
    assert result is True
    assert "to-delete" not in list_snapshots(snap_dir)


def test_delete_snapshot_missing_returns_false(snap_dir):
    result = delete_snapshot("ghost", directory=snap_dir)
    assert result is False
