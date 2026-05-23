"""Watch and summarize xDS resource state from Envoy's admin API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError

XDS_ENDPOINTS = {
    "clusters": "/clusters?format=json",
    "listeners": "/listeners?format=json",
    "config_dump": "/config_dump",
}


@dataclass
class XdsResourceSummary:
    resource_type: str
    names: List[str] = field(default_factory=list)
    count: int = 0
    raw: Optional[Dict] = field(default=None, repr=False)


def fetch_xds_json(admin_url: str, path: str) -> Dict:
    """Fetch JSON from an Envoy admin endpoint."""
    url = admin_url.rstrip("/") + path
    try:
        with urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def summarize_clusters(admin_url: str) -> XdsResourceSummary:
    """Return a summary of active clusters from Envoy."""
    data = fetch_xds_json(admin_url, XDS_ENDPOINTS["clusters"])
    cluster_statuses = data.get("cluster_statuses", [])
    names = [cs.get("name", "<unknown>") for cs in cluster_statuses]
    return XdsResourceSummary(
        resource_type="cluster",
        names=names,
        count=len(names),
        raw=data,
    )


def summarize_listeners(admin_url: str) -> XdsResourceSummary:
    """Return a summary of active listeners from Envoy."""
    data = fetch_xds_json(admin_url, XDS_ENDPOINTS["listeners"])
    listener_statuses = data.get("listener_statuses", [])
    names = [ls.get("name", "<unknown>") for ls in listener_statuses]
    return XdsResourceSummary(
        resource_type="listener",
        names=names,
        count=len(names),
        raw=data,
    )


def watch_xds(admin_url: str) -> Dict[str, XdsResourceSummary]:
    """Return summaries for all tracked xDS resource types."""
    return {
        "clusters": summarize_clusters(admin_url),
        "listeners": summarize_listeners(admin_url),
    }


def format_xds_summary(summaries: Dict[str, XdsResourceSummary]) -> str:
    """Format xDS summaries into a human-readable string."""
    lines = []
    for rtype, summary in summaries.items():
        lines.append(f"{rtype.upper()} ({summary.count}):")
        for name in summary.names:
            lines.append(f"  - {name}")
        if not summary.names:
            lines.append("  (none)")
    return "\n".join(lines)
