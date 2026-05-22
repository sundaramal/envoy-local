"""Bootstrap Envoy configuration templates.

Provides pre-built configuration templates for common Envoy proxy
setups used in local service mesh testing scenarios.
"""

from envoy_local.config import EnvoyConfig, ClusterConfig, ListenerConfig


def simple_http_proxy(
    upstream_host: str,
    upstream_port: int,
    listen_port: int = 10000,
    admin_port: int = 9901,
) -> EnvoyConfig:
    """Create a simple HTTP reverse proxy configuration.

    Routes all traffic on `listen_port` to a single upstream at
    `upstream_host:upstream_port`.

    Args:
        upstream_host: Hostname or IP of the upstream service.
        upstream_port: Port of the upstream service.
        listen_port: Local port Envoy will listen on (default 10000).
        admin_port: Envoy admin API port (default 9901).

    Returns:
        A populated EnvoyConfig instance.
    """
    cfg = EnvoyConfig(admin_port=admin_port)

    cluster = ClusterConfig(
        name="upstream_service",
        host=upstream_host,
        port=upstream_port,
    )
    cfg.add_cluster(cluster)

    listener = ListenerConfig(
        name="ingress",
        port=listen_port,
        route_to_cluster="upstream_service",
    )
    cfg.add_listener(listener)

    return cfg


def multi_cluster_proxy(
    upstreams: list[dict],
    listen_port: int = 10000,
    admin_port: int = 9901,
) -> EnvoyConfig:
    """Create a multi-cluster HTTP proxy configuration.

    Registers multiple upstream clusters. The first cluster in the list
    is used as the default route for the listener.

    Args:
        upstreams: List of dicts with keys ``name``, ``host``, ``port``.
            Example::

                [
                    {"name": "svc_a", "host": "localhost", "port": 8080},
                    {"name": "svc_b", "host": "localhost", "port": 8081},
                ]

        listen_port: Local port Envoy will listen on (default 10000).
        admin_port: Envoy admin API port (default 9901).

    Returns:
        A populated EnvoyConfig instance.

    Raises:
        ValueError: If `upstreams` is empty.
    """
    if not upstreams:
        raise ValueError("At least one upstream must be provided.")

    cfg = EnvoyConfig(admin_port=admin_port)

    for upstream in upstreams:
        cluster = ClusterConfig(
            name=upstream["name"],
            host=upstream["host"],
            port=upstream["port"],
        )
        cfg.add_cluster(cluster)

    # Route listener to the first upstream by default
    default_cluster = upstreams[0]["name"]
    listener = ListenerConfig(
        name="ingress",
        port=listen_port,
        route_to_cluster=default_cluster,
    )
    cfg.add_listener(listener)

    return cfg


def passthrough_tcp(
    upstream_host: str,
    upstream_port: int,
    listen_port: int = 10000,
    admin_port: int = 9901,
) -> EnvoyConfig:
    """Create a TCP passthrough proxy configuration.

    Forwards raw TCP traffic to a single upstream without HTTP inspection.
    Useful for testing non-HTTP services (e.g. gRPC, databases).

    Args:
        upstream_host: Hostname or IP of the upstream service.
        upstream_port: Port of the upstream service.
        listen_port: Local port Envoy will listen on (default 10000).
        admin_port: Envoy admin API port (default 9901).

    Returns:
        A populated EnvoyConfig instance.
    """
    cfg = EnvoyConfig(admin_port=admin_port)

    cluster = ClusterConfig(
        name="tcp_upstream",
        host=upstream_host,
        port=upstream_port,
        # TCP clusters typically use the same STATIC discovery
    )
    cfg.add_cluster(cluster)

    listener = ListenerConfig(
        name="tcp_ingress",
        port=listen_port,
        route_to_cluster="tcp_upstream",
        protocol="tcp",
    )
    cfg.add_listener(listener)

    return cfg


# Registry of built-in template names for CLI discovery
TEMPLATE_REGISTRY: dict[str, str] = {
    "simple-http": "Simple HTTP reverse proxy to a single upstream",
    "multi-cluster": "HTTP proxy with multiple registered upstream clusters",
    "passthrough-tcp": "Raw TCP passthrough to a single upstream",
}
