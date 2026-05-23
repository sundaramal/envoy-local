"""CLI commands for circuit breaker configuration management."""

import json
import sys
from envoy_local.circuit_breaker import (
    CircuitBreakerThresholds,
    validate_circuit_breaker,
    format_circuit_breaker_report,
)


def cmd_cb_validate(args) -> None:
    """Validate circuit breaker thresholds from a JSON file or inline args."""
    try:
        with open(args.config, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: config file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON — {exc}", file=sys.stderr)
        sys.exit(1)

    thresholds = CircuitBreakerThresholds.from_dict(data)
    result = validate_circuit_breaker(thresholds)

    if getattr(args, "json", False):
        output = {
            "valid": result.is_valid,
            "errors": [{"field": e.field, "message": e.message} for e in result.errors],
            "thresholds": thresholds.to_dict(),
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_circuit_breaker_report(thresholds, result))

    if not result.is_valid:
        sys.exit(2)


def cmd_cb_show(args) -> None:
    """Show current circuit breaker defaults."""
    thresholds = CircuitBreakerThresholds()
    result = validate_circuit_breaker(thresholds)

    if getattr(args, "json", False):
        print(json.dumps(thresholds.to_dict(), indent=2))
    else:
        print(format_circuit_breaker_report(thresholds, result))


def register_cb_commands(subparsers) -> None:
    """Register circuit breaker subcommands onto an argparse subparsers object."""
    cb_parser = subparsers.add_parser("circuit-breaker", help="Circuit breaker tools")
    cb_sub = cb_parser.add_subparsers(dest="cb_command")

    validate_p = cb_sub.add_parser("validate", help="Validate a circuit breaker config file")
    validate_p.add_argument("config", help="Path to JSON config file")
    validate_p.add_argument("--json", action="store_true", help="Output as JSON")
    validate_p.set_defaults(func=cmd_cb_validate)

    show_p = cb_sub.add_parser("show", help="Show default circuit breaker thresholds")
    show_p.add_argument("--json", action="store_true", help="Output as JSON")
    show_p.set_defaults(func=cmd_cb_show)
