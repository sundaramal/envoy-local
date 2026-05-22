"""Inspect and summarize TLS configuration from an EnvoyConfig."""

from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.config import EnvoyConfig


@dataclass
class TLSInspectionResult:
    listener_name: str
    port: int
    tls_enabled: bool
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


def inspect_listener_tls(listener: dict) -> TLSInspectionResult:
    """Inspect a single listener dict for TLS settings."""
    name = listener.get("name", "<unnamed>")
    port = listener.get("port", 0)
    tls_context = listener.get("tls_context", None)
    warnings = []

    if tls_context is None:
        return TLSInspectionResult(
            listener_name=name,
            port=port,
            tls_enabled=False,
            warnings=["No TLS context configured; traffic will be plaintext."],
        )

    cert_path = tls_context.get("cert_chain_file")
    key_path = tls_context.get("private_key_file")

    if not cert_path:
        warnings.append("TLS context present but cert_chain_file is missing.")
    if not key_path:
        warnings.append("TLS context present but private_key_file is missing.")

    return TLSInspectionResult(
        listener_name=name,
        port=port,
        tls_enabled=True,
        cert_path=cert_path,
        key_path=key_path,
        warnings=warnings,
    )


def inspect_config_tls(config: EnvoyConfig) -> List[TLSInspectionResult]:
    """Return TLS inspection results for all listeners in an EnvoyConfig."""
    results = []
    for listener in config.listeners:
        raw = {
            "name": listener.name,
            "port": listener.port,
            "tls_context": getattr(listener, "tls_context", None),
        }
        results.append(inspect_listener_tls(raw))
    return results


def format_tls_report(results: List[TLSInspectionResult]) -> str:
    """Format TLS inspection results as a human-readable string."""
    lines = ["TLS Inspection Report", "=" * 40]
    for r in results:
        status = "ENABLED" if r.tls_enabled else "DISABLED"
        lines.append(f"Listener: {r.listener_name} (port {r.port}) — TLS {status}")
        if r.cert_path:
            lines.append(f"  cert: {r.cert_path}")
        if r.key_path:
            lines.append(f"  key:  {r.key_path}")
        for w in r.warnings:
            lines.append(f"  [WARN] {w}")
    return "\n".join(lines)
