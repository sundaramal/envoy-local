"""Track and report endpoint (upstream host) changes over time."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EndpointSnapshot:
    cluster: str
    addresses: List[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "cluster": self.cluster,
            "addresses": self.addresses,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict) -> "EndpointSnapshot":
        return EndpointSnapshot(
            cluster=data["cluster"],
            addresses=data["addresses"],
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass
class EndpointDiff:
    cluster: str
    added: List[str]
    removed: List[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)


def diff_snapshots(
    before: EndpointSnapshot, after: EndpointSnapshot
) -> EndpointDiff:
    """Return addresses added and removed between two snapshots."""
    before_set = set(before.addresses)
    after_set = set(after.addresses)
    return EndpointDiff(
        cluster=after.cluster,
        added=sorted(after_set - before_set),
        removed=sorted(before_set - after_set),
    )


def parse_endpoints_from_clusters(clusters_json: dict) -> List[EndpointSnapshot]:
    """Extract EndpointSnapshot list from Envoy /clusters?format=json payload."""
    snapshots: List[EndpointSnapshot] = []
    for entry in clusters_json.get("cluster_statuses", []):
        name = entry.get("name", "unknown")
        addresses: List[str] = []
        for host in entry.get("host_statuses", []):
            addr = host.get("address", {}).get("socket_address", {})
            ip = addr.get("address", "")
            port = addr.get("port_value", "")
            if ip and port:
                addresses.append(f"{ip}:{port}")
        snapshots.append(EndpointSnapshot(cluster=name, addresses=addresses))
    return snapshots


def format_diff(diff: EndpointDiff) -> str:
    """Return a human-readable string describing endpoint changes."""
    if not diff.has_changes:
        return f"[{diff.cluster}] no endpoint changes"
    lines = [f"[{diff.cluster}] endpoint changes:"]
    for addr in diff.added:
        lines.append(f"  + {addr}")
    for addr in diff.removed:
        lines.append(f"  - {addr}")
    return "\n".join(lines)
