"""CLI commands for inspecting and validating retry policies."""

import json
import sys
from typing import Any

from envoy_local.retry_policy import RetryPolicy, validate_retry_policy


def cmd_retry_validate(args: Any) -> None:
    """Validate a retry policy from a JSON string or file."""
    try:
        if args.file:
            with open(args.file) as fh:
                data = json.load(fh)
        else:
            data = json.loads(args.json)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    policy = RetryPolicy.from_dict(data)
    errors = validate_retry_policy(policy)

    if args.output == "json":
        print(json.dumps({"valid": len(errors) == 0, "errors": errors}, indent=2))
    else:
        if errors:
            print("Retry policy is INVALID:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(2)
        else:
            print("Retry policy is valid.")


def cmd_retry_show(args: Any) -> None:
    """Display the effective retry policy as Envoy config dict."""
    try:
        if args.file:
            with open(args.file) as fh:
                data = json.load(fh)
        else:
            data = json.loads(args.json)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    policy = RetryPolicy.from_dict(data)
    print(json.dumps(policy.to_dict(), indent=2))


def register_retry_commands(subparsers: Any) -> None:
    p_validate = subparsers.add_parser("retry-validate", help="Validate a retry policy")
    p_validate.add_argument("--file", default=None, help="Path to JSON file")
    p_validate.add_argument("--json", default="{}", help="Inline JSON string")
    p_validate.add_argument("--output", choices=["text", "json"], default="text")
    p_validate.set_defaults(func=cmd_retry_validate)

    p_show = subparsers.add_parser("retry-show", help="Show effective retry policy config")
    p_show.add_argument("--file", default=None, help="Path to JSON file")
    p_show.add_argument("--json", default="{}", help="Inline JSON string")
    p_show.set_defaults(func=cmd_retry_show)
