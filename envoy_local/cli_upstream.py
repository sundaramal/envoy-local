"""CLI commands for upstream cluster health inspection."""

from __future__ import annotations

import json
import sys

from envoy_local.upstream_health import (
    get_upstream_health,
    format_health_report,
    ClusterHealthReport,
)


def cmd_upstream_health(args) -> None:
    """Print health status for all upstream clusters."""
    try:
        reports = get_upstream_health(admin_port=args.admin_port)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = [
            {
                "cluster": r.cluster_name,
                "total_hosts": r.total_hosts,
                "healthy_hosts": r.healthy_hosts,
                "unhealthy_hosts": r.unhealthy_hosts,
                "health_percentage": r.health_percentage,
                "is_healthy": r.is_healthy,
                "hosts": [
                    {
                        "address": h.address,
                        "port": h.port,
                        "healthy": h.healthy,
                        "weight": h.weight,
                    }
                    for h in r.hosts
                ],
            }
            for r in reports
        ]
        print(json.dumps(output, indent=2))
    else:
        print(format_health_report(reports, verbose=getattr(args, "verbose", False)))


def cmd_upstream_summary(args) -> None:
    """Print a one-line summary of cluster health."""
    try:
        reports = get_upstream_health(admin_port=args.admin_port)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    healthy = sum(1 for r in reports if r.is_healthy)
    total = len(reports)
    print(f"Clusters: {healthy}/{total} healthy")


def register_upstream_commands(subparsers) -> None:
    p_health = subparsers.add_parser("upstream-health", help="Show upstream cluster health")
    p_health.add_argument("--admin-port", type=int, default=9901)
    p_health.add_argument("--json", action="store_true", help="Output as JSON")
    p_health.add_argument("--verbose", action="store_true", help="Show per-host detail")
    p_health.set_defaults(func=cmd_upstream_health)

    p_summary = subparsers.add_parser("upstream-summary", help="One-line cluster health summary")
    p_summary.add_argument("--admin-port", type=int, default=9901)
    p_summary.set_defaults(func=cmd_upstream_summary)
