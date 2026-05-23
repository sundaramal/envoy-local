"""Upstream cluster health checking utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError


@dataclass
class HostHealthStatus:
    address: str
    port: int
    healthy: bool
    weight: int = 1
    zone: str = ""


@dataclass
class ClusterHealthReport:
    cluster_name: str
    total_hosts: int = 0
    healthy_hosts: int = 0
    unhealthy_hosts: int = 0
    hosts: List[HostHealthStatus] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.healthy_hosts > 0

    @property
    def health_percentage(self) -> float:
        if self.total_hosts == 0:
            return 0.0
        return round(self.healthy_hosts / self.total_hosts * 100, 1)


def fetch_clusters_json(admin_port: int = 9901) -> dict:
    url = f"http://localhost:{admin_port}/clusters?format=json"
    try:
        with urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (URLError, Exception) as exc:
        raise RuntimeError(f"Failed to fetch clusters from admin API: {exc}") from exc


def parse_cluster_health(raw: dict) -> List[ClusterHealthReport]:
    reports: Dict[str, ClusterHealthReport] = {}
    for entry in raw.get("cluster_statuses", []):
        name = entry.get("name", "unknown")
        report = ClusterHealthReport(cluster_name=name)
        for host_status in entry.get("host_statuses", []):
            addr = host_status.get("address", {}).get("socket_address", {})
            hhs = HostHealthStatus(
                address=addr.get("address", ""),
                port=addr.get("port_value", 0),
                healthy=host_status.get("health_status", {}).get("eds_health_status", "") != "UNHEALTHY",
                weight=host_status.get("weight", 1),
            )
            report.hosts.append(hhs)
            report.total_hosts += 1
            if hhs.healthy:
                report.healthy_hosts += 1
            else:
                report.unhealthy_hosts += 1
        reports[name] = report
    return list(reports.values())


def get_upstream_health(admin_port: int = 9901) -> List[ClusterHealthReport]:
    raw = fetch_clusters_json(admin_port)
    return parse_cluster_health(raw)


def format_health_report(reports: List[ClusterHealthReport], verbose: bool = False) -> str:
    if not reports:
        return "No clusters found."
    lines = []
    for r in reports:
        status = "HEALTHY" if r.is_healthy else "DEGRADED"
        lines.append(f"[{status}] {r.cluster_name}: {r.healthy_hosts}/{r.total_hosts} hosts ({r.health_percentage}%)")
        if verbose:
            for h in r.hosts:
                hstatus = "UP" if h.healthy else "DOWN"
                lines.append(f"    {hstatus} {h.address}:{h.port} (weight={h.weight})")
    return "\n".join(lines)
