"""CLI commands for managing and validating timeout policies."""

import json
import sys

from envoy_local.timeout_policy import (
    TimeoutPolicy,
    from_dict,
    to_dict,
    validate_timeout_policy,
)


def cmd_timeout_validate(args) -> None:
    policy = TimeoutPolicy(
        connect_timeout_ms=args.connect_timeout_ms,
        request_timeout_ms=args.request_timeout_ms,
        idle_timeout_ms=args.idle_timeout_ms,
        max_stream_duration_ms=args.max_stream_duration_ms,
    )
    result = validate_timeout_policy(policy)

    if getattr(args, "json", False):
        print(json.dumps({
            "valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }))
    else:
        if result.is_valid:
            print("Timeout policy is valid.")
        else:
            print("Timeout policy is INVALID:")
            for e in result.errors:
                print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARNING: {w}")

    if not result.is_valid:
        sys.exit(1)


def cmd_timeout_show(args) -> None:
    policy = TimeoutPolicy(
        connect_timeout_ms=args.connect_timeout_ms,
        request_timeout_ms=args.request_timeout_ms,
        idle_timeout_ms=args.idle_timeout_ms,
        max_stream_duration_ms=args.max_stream_duration_ms,
    )
    d = to_dict(policy)
    if getattr(args, "json", False):
        print(json.dumps(d))
    else:
        for k, v in d.items():
            print(f"  {k}: {v}")


def register_timeout_commands(subparsers) -> None:
    parent = subparsers.add_parser("timeout", help="Manage timeout policies")
    sub = parent.add_subparsers(dest="timeout_cmd")

    for name, fn in [("validate", cmd_timeout_validate), ("show", cmd_timeout_show)]:
        p = sub.add_parser(name)
        p.add_argument("--connect-timeout-ms", dest="connect_timeout_ms", type=int, default=1000)
        p.add_argument("--request-timeout-ms", dest="request_timeout_ms", type=int, default=None)
        p.add_argument("--idle-timeout-ms", dest="idle_timeout_ms", type=int, default=None)
        p.add_argument("--max-stream-duration-ms", dest="max_stream_duration_ms", type=int, default=None)
        p.add_argument("--json", action="store_true", default=False)
        p.set_defaults(func=fn)
