"""Network policy enforcement rules for Envoy listener/cluster configurations."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PolicyRule:
    name: str
    allow_ports: List[int] = field(default_factory=list)
    deny_ports: List[int] = field(default_factory=list)
    allow_hosts: List[str] = field(default_factory=list)
    deny_hosts: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class PolicyViolation:
    rule_name: str
    message: str
    severity: str = "error"  # "error" or "warning"


@dataclass
class PolicyReport:
    violations: List[PolicyViolation] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return not any(v.severity == "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")


def _check_port_policy(
    rule: PolicyRule, port: int, context: str
) -> Optional[PolicyViolation]:
    if rule.deny_ports and port in rule.deny_ports:
        return PolicyViolation(
            rule_name=rule.name,
            message=f"{context} uses denied port {port}",
            severity="error",
        )
    if rule.allow_ports and port not in rule.allow_ports:
        return PolicyViolation(
            rule_name=rule.name,
            message=f"{context} port {port} not in allowed list",
            severity="warning",
        )
    return None


def _check_host_policy(
    rule: PolicyRule, host: str, context: str
) -> Optional[PolicyViolation]:
    if rule.deny_hosts and host in rule.deny_hosts:
        return PolicyViolation(
            rule_name=rule.name,
            message=f"{context} uses denied host '{host}'",
            severity="error",
        )
    if rule.allow_hosts and host not in rule.allow_hosts:
        return PolicyViolation(
            rule_name=rule.name,
            message=f"{context} host '{host}' not in allowed list",
            severity="warning",
        )
    return None


def evaluate_policy(config: dict, rules: List[PolicyRule]) -> PolicyReport:
    """Evaluate network policy rules against an Envoy config dict."""
    report = PolicyReport()

    listeners = config.get("static_resources", {}).get("listeners", [])
    clusters = config.get("static_resources", {}).get("clusters", [])

    for rule in rules:
        for listener in listeners:
            port = listener.get("address", {}).get("socket_address", {}).get("port_value")
            if port is not None:
                violation = _check_port_policy(rule, port, f"Listener '{listener.get('name', '?')}'")
                if violation:
                    report.violations.append(violation)

        for cluster in clusters:
            for endpoint in cluster.get("load_assignment", {}).get("endpoints", []):
                for lb in endpoint.get("lb_endpoints", []):
                    addr = lb.get("endpoint", {}).get("address", {}).get("socket_address", {})
                    host = addr.get("address")
                    port = addr.get("port_value")
                    ctx = f"Cluster '{cluster.get('name', '?')}'"
                    if host:
                        v = _check_host_policy(rule, host, ctx)
                        if v:
                            report.violations.append(v)
                    if port is not None:
                        v = _check_port_policy(rule, port, ctx)
                        if v:
                            report.violations.append(v)

    return report
