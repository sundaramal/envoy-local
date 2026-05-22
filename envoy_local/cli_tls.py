"""CLI commands for TLS inspection."""

import argparse
import json
import sys

from envoy_local.tls_inspector import inspect_listener_tls, format_tls_report


def cmd_tls_inspect(args: argparse.Namespace) -> None:
    """Inspect TLS settings from a raw listener definition (JSON file or stdin)."""
    if args.file:
        try:
            with open(args.file) as fh:
                listener_data = json.load(fh)
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON — {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            listener_data = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON on stdin — {exc}", file=sys.stderr)
            sys.exit(1)

    listeners = listener_data if isinstance(listener_data, list) else [listener_data]
    results = [inspect_listener_tls(l) for l in listeners]

    if args.json:
        output = [
            {
                "listener": r.listener_name,
                "port": r.port,
                "tls_enabled": r.tls_enabled,
                "cert_path": r.cert_path,
                "key_path": r.key_path,
                "warnings": r.warnings,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print(format_tls_report(results))

    has_warnings = any(r.warnings for r in results)
    if has_warnings:
        sys.exit(2)


def register_tls_commands(subparsers) -> None:
    """Register TLS sub-commands onto an existing argparse subparsers object."""
    p = subparsers.add_parser("tls-inspect", help="Inspect TLS config for listeners")
    p.add_argument(
        "--file", "-f", default=None,
        help="Path to JSON listener file (default: stdin)",
    )
    p.add_argument(
        "--json", action="store_true",
        help="Output results as JSON",
    )
    p.set_defaults(func=cmd_tls_inspect)
