"""CLI commands for endpoint tracking."""

from __future__ import annotations

import json
import sys
from urllib.error import URLError
from urllib.request import urlopen

from envoy_local.endpoint_tracker import (
    EndpointSnapshot,
    diff_snapshots,
    format_diff,
    parse_endpoints_from_clusters,
)


def _fetch_snapshots(admin_url: str) -> list[EndpointSnapshot]:
    url = admin_url.rstrip("/") + "/clusters?format=json"
    with urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    return parse_endpoints_from_clusters(data)


def cmd_endpoint_list(args) -> None:
    """List current endpoints for all clusters."""
    try:
        snapshots = _fetch_snapshots(args.admin_url)
    except (URLError, OSError) as exc:
        print(f"error: could not reach admin API: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps([s.to_dict() for s in snapshots], indent=2))
        return

    if not snapshots:
        print("no clusters found")
        return

    for snap in snapshots:
        addrs = ", ".join(snap.addresses) if snap.addresses else "(none)"
        print(f"{snap.cluster}: {addrs}")


def cmd_endpoint_diff(args) -> None:
    """Show endpoint changes between two JSON snapshot files."""
    try:
        with open(args.before) as fh:
            before_data = json.load(fh)
        with open(args.after) as fh:
            after_data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    before_map = {s["cluster"]: EndpointSnapshot.from_dict(s) for s in before_data}
    after_map = {s["cluster"]: EndpointSnapshot.from_dict(s) for s in after_data}

    all_clusters = sorted(set(before_map) | set(after_map))
    diffs = []
    for cluster in all_clusters:
        b = before_map.get(cluster, EndpointSnapshot(cluster=cluster, addresses=[]))
        a = after_map.get(cluster, EndpointSnapshot(cluster=cluster, addresses=[]))
        diffs.append(diff_snapshots(b, a))

    if args.json:
        output = [
            {"cluster": d.cluster, "added": d.added, "removed": d.removed}
            for d in diffs
        ]
        print(json.dumps(output, indent=2))
        return

    for d in diffs:
        print(format_diff(d))


def register_endpoint_commands(subparsers) -> None:
    p_list = subparsers.add_parser("endpoint-list", help="list current endpoints")
    p_list.add_argument("--admin-url", default="http://localhost:9901")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=cmd_endpoint_list)

    p_diff = subparsers.add_parser("endpoint-diff", help="diff two endpoint snapshots")
    p_diff.add_argument("before", help="path to before snapshot JSON")
    p_diff.add_argument("after", help="path to after snapshot JSON")
    p_diff.add_argument("--json", action="store_true")
    p_diff.set_defaults(func=cmd_endpoint_diff)
