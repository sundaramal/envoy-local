"""Entry point for envoy-local CLI.

Allows the package to be invoked directly via:
    python -m envoy_local <command> [options]
"""

import argparse
import sys

from envoy_local.cli import cmd_start, cmd_stop, cmd_status, cmd_stats
from envoy_local.cli_snapshot import (
    cmd_snapshot_save,
    cmd_snapshot_load,
    cmd_snapshot_list,
    cmd_snapshot_delete,
)


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser with all sub-commands."""
    parser = argparse.ArgumentParser(
        prog="envoy-local",
        description="Spin up and manage local Envoy proxy configurations for service mesh testing.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # --- start ---
    p_start = subparsers.add_parser("start", help="Start a local Envoy proxy instance.")
    p_start.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to an envoy-local JSON config file (optional).",
    )
    p_start.add_argument(
        "--admin-port",
        type=int,
        default=9901,
        metavar="PORT",
        help="Envoy admin listener port (default: 9901).",
    )
    p_start.add_argument(
        "--binary",
        default="envoy",
        metavar="PATH",
        help="Path to the Envoy binary (default: envoy).",
    )
    p_start.set_defaults(func=cmd_start)

    # --- stop ---
    p_stop = subparsers.add_parser("stop", help="Stop the running Envoy proxy instance.")
    p_stop.set_defaults(func=cmd_stop)

    # --- status ---
    p_status = subparsers.add_parser("status", help="Show health status of the running proxy.")
    p_status.add_argument(
        "--admin-port",
        type=int,
        default=9901,
        metavar="PORT",
        help="Envoy admin listener port (default: 9901).",
    )
    p_status.set_defaults(func=cmd_status)

    # --- stats ---
    p_stats = subparsers.add_parser("stats", help="Fetch and display Envoy statistics.")
    p_stats.add_argument(
        "--admin-port",
        type=int,
        default=9901,
        metavar="PORT",
        help="Envoy admin listener port (default: 9901).",
    )
    p_stats.add_argument(
        "--filter",
        dest="stat_filter",
        metavar="PREFIX",
        default=None,
        help="Only show stats whose names start with PREFIX.",
    )
    p_stats.set_defaults(func=cmd_stats)

    # --- snapshot sub-group ---
    p_snap = subparsers.add_parser("snapshot", help="Manage configuration snapshots.")
    snap_sub = p_snap.add_subparsers(dest="snap_command", metavar="<subcommand>")
    snap_sub.required = True

    ps_save = snap_sub.add_parser("save", help="Save the current configuration as a snapshot.")
    ps_save.add_argument("--name", default=None, help="Snapshot name (auto-generated if omitted).")
    ps_save.set_defaults(func=cmd_snapshot_save)

    ps_load = snap_sub.add_parser("load", help="Load a snapshot and apply it.")
    ps_load.add_argument("name", help="Name of the snapshot to load.")
    ps_load.set_defaults(func=cmd_snapshot_load)

    ps_list = snap_sub.add_parser("list", help="List all available snapshots.")
    ps_list.set_defaults(func=cmd_snapshot_list)

    ps_delete = snap_sub.add_parser("delete", help="Delete a named snapshot.")
    ps_delete.add_argument("name", help="Name of the snapshot to delete.")
    ps_delete.set_defaults(func=cmd_snapshot_delete)

    return parser


def main(argv=None):
    """Parse arguments and dispatch to the appropriate command handler."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        exit_code = args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        exit_code = 130

    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
