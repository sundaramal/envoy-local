"""Utility to scan and report on ports used by Envoy listeners and clusters."""

import socket
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PortScanResult:
    port: int
    host: str
    is_open: bool
    label: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ScanReport:
    results: List[PortScanResult] = field(default_factory=list)

    @property
    def open_ports(self) -> List[PortScanResult]:
        return [r for r in self.results if r.is_open]

    @property
    def closed_ports(self) -> List[PortScanResult]:
        return [r for r in self.results if not r.is_open]


def probe_port(host: str, port: int, timeout: float = 1.0, label: Optional[str] = None) -> PortScanResult:
    """Attempt a TCP connection to host:port and return the result."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return PortScanResult(port=port, host=host, is_open=True, label=label)
    except (ConnectionRefusedError, OSError) as exc:
        return PortScanResult(port=port, host=host, is_open=False, label=label, error=str(exc))


def scan_config_ports(config: dict, host: str = "127.0.0.1", timeout: float = 1.0) -> ScanReport:
    """Scan all listener and admin ports found in an Envoy config dict."""
    report = ScanReport()

    admin_port = config.get("admin", {}).get("address", {}).get("socket_address", {}).get("port_value")
    if admin_port:
        report.results.append(probe_port(host, int(admin_port), timeout, label="admin"))

    for resource in config.get("static_resources", {}).get("listeners", []):
        port = (
            resource.get("address", {})
            .get("socket_address", {})
            .get("port_value")
        )
        name = resource.get("name", "listener")
        if port:
            report.results.append(probe_port(host, int(port), timeout, label=name))

    return report


def format_scan_report(report: ScanReport) -> str:
    """Return a human-readable string summarising the scan report."""
    lines = []
    for r in report.results:
        status = "OPEN" if r.is_open else "CLOSED"
        label = f" ({r.label})" if r.label else ""
        detail = f" — {r.error}" if r.error else ""
        lines.append(f"  {r.host}:{r.port}{label}: {status}{detail}")
    open_count = len(report.open_ports)
    total = len(report.results)
    lines.append(f"\n{open_count}/{total} port(s) open.")
    return "\n".join(lines)
