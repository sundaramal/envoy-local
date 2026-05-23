"""CLI commands for managing header rewrite rules."""
from __future__ import annotations

import json
import sys
from typing import List

from envoy_local.header_rewrite import (
    HeaderRewriteRule,
    rules_to_envoy_headers,
    validate_rules,
)


def _parse_rules_from_args(args) -> List[HeaderRewriteRule]:
    rules = []
    for entry in args.rules:
        parts = entry.split(":", 2)
        if len(parts) < 2:
            print(f"[error] Invalid rule format: '{entry}'. Expected action:header[:value]",
                  file=sys.stderr)
            sys.exit(1)
        action = parts[0].strip()
        header = parts[1].strip()
        value = parts[2].strip() if len(parts) == 3 else None
        rules.append(HeaderRewriteRule(action=action, header=header, value=value))
    return rules


def cmd_header_validate(args) -> None:
    """Validate a set of header rewrite rules."""
    rules = _parse_rules_from_args(args)
    result = validate_rules(rules)

    if getattr(args, "json", False):
        print(json.dumps({
            "valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }, indent=2))
    else:
        if result.is_valid:
            print("[ok] All header rewrite rules are valid.")
        else:
            for e in result.errors:
                print(f"[error] {e}")
        for w in result.warnings:
            print(f"[warn]  {w}")

    if not result.is_valid:
        sys.exit(1)


def cmd_header_show(args) -> None:
    """Show the Envoy-formatted header config for the given rules."""
    rules = _parse_rules_from_args(args)
    envoy_headers = rules_to_envoy_headers(rules)
    print(json.dumps(envoy_headers, indent=2))


def register_header_commands(subparsers) -> None:
    p_validate = subparsers.add_parser(
        "header-validate", help="Validate header rewrite rules"
    )
    p_validate.add_argument(
        "rules", nargs="+",
        metavar="ACTION:HEADER[:VALUE]",
        help="Rules in the form action:header or action:header:value",
    )
    p_validate.add_argument("--json", action="store_true", help="JSON output")
    p_validate.set_defaults(func=cmd_header_validate)

    p_show = subparsers.add_parser(
        "header-show", help="Show Envoy header config for rules"
    )
    p_show.add_argument(
        "rules", nargs="+",
        metavar="ACTION:HEADER[:VALUE]",
    )
    p_show.set_defaults(func=cmd_header_show)
