"""CLI commands for diffing Envoy config snapshots or files."""

import json
import sys

from envoy_local.diff import diff_configs, format_diff
from envoy_local.snapshot import load_snapshot


def cmd_diff_snapshots(args) -> int:
    """Diff two named snapshots."""
    try:
        old = load_snapshot(args.snapshot_a, snapshots_dir=args.snapshots_dir)
        new = load_snapshot(args.snapshot_b, snapshots_dir=args.snapshots_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = diff_configs(old, new)

    if args.json:
        output = {
            "added": result.added,
            "removed": result.removed,
            "changed": [
                {"key": k, "old": o, "new": n} for k, o, n in result.changed
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_diff(result))

    return 0 if not result.has_changes else 2


def cmd_diff_files(args) -> int:
    """Diff two JSON config files."""
    try:
        with open(args.file_a) as f:
            old = json.load(f)
        with open(args.file_b) as f:
            new = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = diff_configs(old, new)

    if args.json:
        output = {
            "added": result.added,
            "removed": result.removed,
            "changed": [
                {"key": k, "old": o, "new": n} for k, o, n in result.changed
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_diff(result))

    return 0 if not result.has_changes else 2


def register_diff_commands(subparsers):
    p_snap = subparsers.add_parser("diff-snapshots", help="Diff two config snapshots")
    p_snap.add_argument("snapshot_a", help="Name of the first snapshot")
    p_snap.add_argument("snapshot_b", help="Name of the second snapshot")
    p_snap.add_argument("--snapshots-dir", default=None)
    p_snap.add_argument("--json", action="store_true", help="Output as JSON")
    p_snap.set_defaults(func=cmd_diff_snapshots)

    p_file = subparsers.add_parser("diff-files", help="Diff two JSON config files")
    p_file.add_argument("file_a", help="Path to the first config file")
    p_file.add_argument("file_b", help="Path to the second config file")
    p_file.add_argument("--json", action="store_true", help="Output as JSON")
    p_file.set_defaults(func=cmd_diff_files)
