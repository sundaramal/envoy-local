"""Configuration management for envoy-local.

Handles loading, validating, and writing Envoy proxy configuration
files used during local service mesh testing.
"""

import os
import yaml
from dataclasses import dataclass, field, asdict
from typing import List, Optional


DEFAULT_ADMIN_PORT = 9901
DEFAULT_LISTEN_PORT = 10000
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.envoy-local/envoy.yaml")


@dataclass
class ClusterConfig:
    name: str
    address: str
    port: int
    connect_timeout: str = "1s"


@dataclass
class ListenerConfig:
    name: str
    address: str = "0.0.0.0"
    port: int = DEFAULT_LISTEN_PORT
    route_to_cluster: str = ""


@dataclass
class EnvoyConfig:
    admin_port: int = DEFAULT_ADMIN_PORT
    listeners: List[ListenerConfig] = field(default_factory=list)
    clusters: List[ClusterConfig] = field(default_factory=list)
    config_path: str = DEFAULT_CONFIG_PATH

    def add_cluster(self, name: str, address: str, port: int, connect_timeout: str = "1s") -> ClusterConfig:
        cluster = ClusterConfig(name=name, address=address, port=port, connect_timeout=connect_timeout)
        self.clusters.append(cluster)
        return cluster

    def add_listener(self, name: str, port: int, route_to_cluster: str, address: str = "0.0.0.0") -> ListenerConfig:
        listener = ListenerConfig(name=name, address=address, port=port, route_to_cluster=route_to_cluster)
        self.listeners.append(listener)
        return listener

    def to_envoy_yaml(self) -> dict:
        """Render the config as an Envoy-compatible YAML structure."""
        return {
            "admin": {
                "address": {
                    "socket_address": {"address": "127.0.0.1", "port_value": self.admin_port}
                }
            },
            "static_resources": {
                "listeners": [
                    {
                        "name": ln.name,
                        "address": {
                            "socket_address": {"address": ln.address, "port_value": ln.port}
                        },
                        "filter_chains": [
                            {
                                "filters": [
                                    {
                                        "name": "envoy.filters.network.http_connection_manager",
                                        "typed_config": {
                                            "@type": "type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager",
                                            "stat_prefix": ln.name,
                                            "route_config": {
                                                "virtual_hosts": [
                                                    {
                                                        "name": "local",
                                                        "domains": ["*"],
                                                        "routes": [
                                                            {
                                                                "match": {"prefix": "/"},
                                                                "route": {"cluster": ln.route_to_cluster},
                                                            }
                                                        ],
                                                    }
                                                ]
                                            },
                                            "http_filters": [{"name": "envoy.filters.http.router", "typed_config": {"@type": "type.googleapis.com/envoy.extensions.filters.http.router.v3.Router"}}],
                                        },
                                    }
                                ]
                            }
                        ],
                    }
                    for ln in self.listeners
                ],
                "clusters": [
                    {
                        "name": cl.name,
                        "connect_timeout": cl.connect_timeout,
                        "load_assignment": {
                            "cluster_name": cl.name,
                            "endpoints": [
                                {
                                    "lb_endpoints": [
                                        {
                                            "endpoint": {
                                                "address": {
                                                    "socket_address": {"address": cl.address, "port_value": cl.port}
                                                }
                                            }
                                        }
                                    ]
                                }
                            ],
                        },
                    }
                    for cl in self.clusters
                ],
            },
        }

    def write(self, path: Optional[str] = None) -> str:
        """Write the Envoy YAML config to disk. Returns the path written."""
        target = path or self.config_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w") as f:
            yaml.dump(self.to_envoy_yaml(), f, default_flow_style=False, sort_keys=False)
        return target

    @classmethod
    def load(cls, path: str) -> "EnvoyConfig":
        """Load an EnvoyConfig from an existing YAML file."""
        with open(path) as f:
            raw = yaml.safe_load(f)
        cfg = cls(config_path=path)
        cfg.admin_port = raw["admin"]["address"]["socket_address"]["port_value"]
        for cl in raw.get("static_resources", {}).get("clusters", []):
            ep = cl["load_assignment"]["endpoints"][0]["lb_endpoints"][0]["endpoint"]["address"]["socket_address"]
            cfg.clusters.append(ClusterConfig(name=cl["name"], address=ep["address"], port=ep["port_value"], connect_timeout=cl.get("connect_timeout", "1s")))
        return cfg
