"""Tests for envoy_local.route_validator."""

import pytest

from envoy_local.config import EnvoyConfig, ClusterConfig, ListenerConfig
from envoy_local.route_validator import (
    ValidationResult,
    validate_cluster_names,
    validate_listener_ports,
    validate_cluster_endpoints,
    validate_config,
)


@pytest.fixture
def valid_config():
    cfg = EnvoyConfig()
    cfg.clusters = [
        ClusterConfig(name="backend", endpoints=[{"address": "127.0.0.1", "port": 8080}]),
    ]
    cfg.listeners = [
        ListenerConfig(name="ingress", port=10000),
    ]
    return cfg


def test_valid_config_passes(valid_config):
    result = validate_config(valid_config)
    assert result.valid is True
    assert result.errors == []


def test_duplicate_cluster_name_is_error(valid_config):
    valid_config.clusters.append(
        ClusterConfig(name="backend", endpoints=[{"address": "10.0.0.1", "port": 9090}])
    )
    result = validate_cluster_names(valid_config)
    assert result.valid is False
    assert any("Duplicate cluster" in e for e in result.errors)


def test_empty_cluster_name_is_error(valid_config):
    valid_config.clusters.append(
        ClusterConfig(name="", endpoints=[{"address": "10.0.0.1", "port": 9090}])
    )
    result = validate_cluster_names(valid_config)
    assert result.valid is False
    assert any("empty name" in e for e in result.errors)


def test_invalid_listener_port_is_error(valid_config):
    valid_config.listeners.append(ListenerConfig(name="bad", port=99999))
    result = validate_listener_ports(valid_config)
    assert result.valid is False
    assert any("invalid port" in e for e in result.errors)


def test_duplicate_listener_port_is_error(valid_config):
    valid_config.listeners.append(ListenerConfig(name="second", port=10000))
    result = validate_listener_ports(valid_config)
    assert result.valid is False
    assert any("Duplicate listener port" in e for e in result.errors)


def test_privileged_port_produces_warning(valid_config):
    valid_config.listeners.append(ListenerConfig(name="priv", port=443))
    result = validate_listener_ports(valid_config)
    assert result.valid is True
    assert any("privileged port" in w for w in result.warnings)


def test_cluster_with_no_endpoints_is_error(valid_config):
    valid_config.clusters.append(ClusterConfig(name="empty", endpoints=[]))
    result = validate_cluster_endpoints(valid_config)
    assert result.valid is False
    assert any("no endpoints" in e for e in result.errors)


def test_endpoint_with_no_address_is_error(valid_config):
    valid_config.clusters.append(
        ClusterConfig(name="noaddr", endpoints=[{"address": "", "port": 8080}])
    )
    result = validate_cluster_endpoints(valid_config)
    assert result.valid is False
    assert any("no address" in e for e in result.errors)


def test_endpoint_with_bad_port_is_error(valid_config):
    valid_config.clusters.append(
        ClusterConfig(name="badport", endpoints=[{"address": "1.2.3.4", "port": 0}])
    )
    result = validate_cluster_endpoints(valid_config)
    assert result.valid is False
    assert any("invalid port" in e for e in result.errors)
