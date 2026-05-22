"""CLI commands for Envoy log management."""

import sys

from envoy_local.logs import (
    get_log_path,
    tail_log,
    filter_log_by_level,
    clear_log,
    DEFAULT_LOG_DIR,
)


def cmd_logs_tail(args) -> int:
    """Print the last N lines of the Envoy log file."""
    log_path = get_log_path(log_dir=getattr(args, "log_dir", DEFAULT_LOG_DIR))
    lines_count = getattr(args, "lines", 50)
    try:
        lines = tail_log(log_path, lines=lines_count)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


def cmd_logs_filter(args) -> int:
    """Print log lines matching a specific log level."""
    log_path = get_log_path(log_dir=getattr(args, "log_dir", DEFAULT_LOG_DIR))
    level = getattr(args, "level", "error")
    try:
        lines = filter_log_by_level(log_path, level)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not lines:
        print(f"No log entries found for level: {level}")
        return 0
    for line in lines:
        print(line)
    return 0


def cmd_logs_clear(args) -> int:
    """Truncate the Envoy log file."""
    log_path = get_log_path(log_dir=getattr(args, "log_dir", DEFAULT_LOG_DIR))
    try:
        clear_log(log_path)
        print(f"Log cleared: {log_path}")
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_logs_path(args) -> int:
    """Print the path to the current Envoy log file."""
    log_path = get_log_path(log_dir=getattr(args, "log_dir", DEFAULT_LOG_DIR))
    print(log_path)
    return 0
