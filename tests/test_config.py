"""Tests for envoy_local.config module."""

import os
import tempfile
import yaml
import pytest

from envoy_local.config import (
    EnvoyConfig,
    ClusterConfig,
    ListenerConfig,
    DEFAULT_ADMIN_PORT,
    DEFAULT_LISTEN_PORT,
)


@pytest.fixture
def basic_config():
    cfg = EnvoyConfig(admin_port=9901)
    cfg.add_cluster("backend", "127.0.0.1", 8080)
    cfg.add_listener("ingress", 10000, "backend")
    return cfg


def test_default_admin_port():
    cfg = EnvoyConfig()
    assert cfg.admin_port == DEFAULT_ADMIN_PORT


def test_add_cluster(basic_config):
    assert len(basic_config.clusters) == 1
    cluster = basic_config.clusters[0]
    assert cluster.name == "backend"
    assert cluster.address == "127.0.0.1"
    assert cluster.port == 8080
    assert cluster.connect_timeout == "1s"


def test_add_listener(basic_config):
    assert len(basic_config.listeners) == 1
    listener = basic_config.listeners[0]
    assert listener.name == "ingress"
    assert listener.port == 10000
    assert listener.route_to_cluster == "backend"
    assert listener.address == "0.0.0.0"


def test_to_envoy_yaml_structure(basic_config):
    rendered = basic_config.to_envoy_yaml()
    assert "admin" in rendered
    assert rendered["admin"]["address"]["socket_address"]["port_value"] == 9901
    assert "static_resources" in rendered
    clusters = rendered["static_resources"]["clusters"]
    listeners = rendered["static_resources"]["listeners"]
    assert len(clusters) == 1
    assert clusters[0]["name"] == "backend"
    assert len(listeners) == 1
    assert listeners[0]["name"] == "ingress"


def test_listener_routes_to_correct_cluster(basic_config):
    rendered = basic_config.to_envoy_yaml()
    listener = rendered["static_resources"]["listeners"][0]
    route = listener["filter_chains"][0]["filters"][0]["typed_config"]["route_config"]["virtual_hosts"][0]["routes"][0]
    assert route["route"]["cluster"] == "backend"


def test_write_creates_valid_yaml(basic_config):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "envoy.yaml")
        written_path = basic_config.write(path)
        assert written_path == path
        assert os.path.exists(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data["admin"]["address"]["socket_address"]["port_value"] == 9901


def test_load_roundtrip(basic_config):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "envoy.yaml")
        basic_config.write(path)
        loaded = EnvoyConfig.load(path)
        assert loaded.admin_port == 9901
        assert len(loaded.clusters) == 1
        assert loaded.clusters[0].name == "backend"
        assert loaded.clusters[0].port == 8080


def test_multiple_clusters_and_listeners():
    cfg = EnvoyConfig()
    cfg.add_cluster("svc-a", "10.0.0.1", 8001, connect_timeout="2s")
    cfg.add_cluster("svc-b", "10.0.0.2", 8002)
    cfg.add_listener("port-a", 9001, "svc-a")
    cfg.add_listener("port-b", 9002, "svc-b")
    rendered = cfg.to_envoy_yaml()
    assert len(rendered["static_resources"]["clusters"]) == 2
    assert len(rendered["static_resources"]["listeners"]) == 2
    assert rendered["static_resources"]["clusters"][0]["connect_timeout"] == "2s"
