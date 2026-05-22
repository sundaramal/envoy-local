"""Validate Envoy route and cluster configurations for common misconfigurations."""

from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.config import EnvoyConfig


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_cluster_names(config: EnvoyConfig) -> ValidationResult:
    """Check that all cluster names are unique and non-empty."""
    result = ValidationResult(valid=True)
    seen = set()
    for cluster in config.clusters:
        if not cluster.name:
            result.add_error("Cluster has an empty name.")
            continue
        if cluster.name in seen:
            result.add_error(f"Duplicate cluster name: '{cluster.name}'.")
        seen.add(cluster.name)
    return result


def validate_listener_ports(config: EnvoyConfig) -> ValidationResult:
    """Check that listener ports are in valid range and unique."""
    result = ValidationResult(valid=True)
    seen_ports = set()
    for listener in config.listeners:
        port = listener.port
        if not (1 <= port <= 65535):
            result.add_error(
                f"Listener '{listener.name}' has invalid port {port} (must be 1-65535)."
            )
        if port in seen_ports:
            result.add_error(f"Duplicate listener port: {port}.")
        seen_ports.add(port)
        if port < 1024:
            result.add_warning(
                f"Listener '{listener.name}' uses privileged port {port}."
            )
    return result


def validate_cluster_endpoints(config: EnvoyConfig) -> ValidationResult:
    """Check that each cluster has at least one endpoint with a valid port."""
    result = ValidationResult(valid=True)
    for cluster in config.clusters:
        if not cluster.endpoints:
            result.add_error(f"Cluster '{cluster.name}' has no endpoints defined.")
            continue
        for ep in cluster.endpoints:
            host, port = ep.get("address", ""), ep.get("port", 0)
            if not host:
                result.add_error(
                    f"Cluster '{cluster.name}' has an endpoint with no address."
                )
            if not (1 <= port <= 65535):
                result.add_error(
                    f"Cluster '{cluster.name}' endpoint '{host}' has invalid port {port}."
                )
    return result


def validate_config(config: EnvoyConfig) -> ValidationResult:
    """Run all validators and merge results."""
    combined = ValidationResult(valid=True)
    for check in (validate_cluster_names, validate_listener_ports, validate_cluster_endpoints):
        result = check(config)
        combined.errors.extend(result.errors)
        combined.warnings.extend(result.warnings)
        if not result.valid:
            combined.valid = False
    return combined
