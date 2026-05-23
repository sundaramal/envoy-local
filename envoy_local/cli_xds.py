"""CLI commands for xDS resource inspection."""

from __future__ import annotations

import json
import sys

from envoy_local.xds_watch import watch_xds, format_xds_summary


def cmd_xds_watch(args) -> None:
    """Print a summary of live xDS resources from Envoy admin API."""
    admin_url = getattr(args, "admin_url", "http://localhost:9901")
    try:
        summaries = watch_xds(admin_url)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "json", False):
        output = {
            rtype: {
                "count": s.count,
                "names": s.names,
            }
            for rtype, s in summaries.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_xds_summary(summaries))


def cmd_xds_clusters(args) -> None:
    """Print only cluster xDS summary."""
    from envoy_local.xds_watch import summarize_clusters

    admin_url = getattr(args, "admin_url", "http://localhost:9901")
    try:
        summary = summarize_clusters(admin_url)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps({"count": summary.count, "names": summary.names}, indent=2))
    else:
        print(f"Clusters ({summary.count}):")
        for name in summary.names:
            print(f"  - {name}")


def register_xds_commands(subparsers) -> None:
    """Register xds sub-commands onto an argparse subparsers object."""
    p_watch = subparsers.add_parser("xds-watch", help="Show live xDS resource summary")
    p_watch.add_argument("--admin-url", default="http://localhost:9901")
    p_watch.add_argument("--json", action="store_true", help="Output as JSON")
    p_watch.set_defaults(func=cmd_xds_watch)

    p_clusters = subparsers.add_parser("xds-clusters", help="Show live cluster resources")
    p_clusters.add_argument("--admin-url", default="http://localhost:9901")
    p_clusters.add_argument("--json", action="store_true", help="Output as JSON")
    p_clusters.set_defaults(func=cmd_xds_clusters)
