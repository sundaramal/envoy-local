"""CLI commands for network policy evaluation."""

import json
import sys
import yaml

from envoy_local.network_policy import PolicyRule, evaluate_policy


def _load_rules_from_file(path: str):
    """Load policy rules from a JSON or YAML file."""
    with open(path) as f:
        raw = json.load(f) if path.endswith(".json") else yaml.safe_load(f)
    rules = []
    for entry in raw.get("rules", []):
        rules.append(
            PolicyRule(
                name=entry["name"],
                allow_ports=entry.get("allow_ports", []),
                deny_ports=entry.get("deny_ports", []),
                allow_hosts=entry.get("allow_hosts", []),
                deny_hosts=entry.get("deny_hosts", []),
                description=entry.get("description", ""),
            )
        )
    return rules


def cmd_policy_check(args):
    """Evaluate policy rules against a config file."""
    try:
        with open(args.config) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: config file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        rules = _load_rules_from_file(args.policy)
    except FileNotFoundError:
        print(f"Error: policy file '{args.policy}' not found.", file=sys.stderr)
        sys.exit(1)

    report = evaluate_policy(config, rules)

    if getattr(args, "json", False):
        data = [
            {"rule": v.rule_name, "message": v.message, "severity": v.severity}
            for v in report.violations
        ]
        print(json.dumps({"compliant": report.is_compliant, "violations": data}, indent=2))
        return

    if not report.violations:
        print("Policy check passed. No violations found.")
    else:
        for v in report.violations:
            tag = "[ERROR]" if v.severity == "error" else "[WARN] "
            print(f"{tag} [{v.rule_name}] {v.message}")
        print(f"\nResult: {report.error_count} error(s), {report.warning_count} warning(s).")

    if not report.is_compliant:
        sys.exit(2)


def register_policy_commands(subparsers):
    p = subparsers.add_parser("policy-check", help="Evaluate network policy rules against a config")
    p.add_argument("config", help="Path to Envoy config YAML")
    p.add_argument("policy", help="Path to policy rules JSON/YAML")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_policy_check)
