"""Log management utilities for local Envoy instances."""

import os
import re
from pathlib import Path
from typing import Iterator, List, Optional

DEFAULT_LOG_DIR = "/tmp/envoy-local/logs"
DEFAULT_LOG_FILE = "envoy.log"
LOG_LEVEL_PATTERN = re.compile(
    r"\[(trace|debug|info|warning|error|critical)\]", re.IGNORECASE
)


def _ensure_log_dir(log_dir: str = DEFAULT_LOG_DIR) -> str:
    """Create the log directory if it does not exist."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_path(log_dir: str = DEFAULT_LOG_DIR, filename: str = DEFAULT_LOG_FILE) -> str:
    """Return the full path to the Envoy log file."""
    _ensure_log_dir(log_dir)
    return os.path.join(log_dir, filename)


def tail_log(log_path: str, lines: int = 50) -> List[str]:
    """Return the last *lines* lines from the log file."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        all_lines = fh.readlines()
    return [l.rstrip("\n") for l in all_lines[-lines:]]


def filter_log_by_level(log_path: str, level: str) -> List[str]:
    """Return only log lines that match *level* (case-insensitive)."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    target = level.lower()
    matched: List[str] = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = LOG_LEVEL_PATTERN.search(line)
            if m and m.group(1).lower() == target:
                matched.append(line.rstrip("\n"))
    return matched


def clear_log(log_path: str) -> None:
    """Truncate the log file to zero bytes."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")
    with open(log_path, "w") as fh:
        fh.truncate(0)


def iter_log_lines(log_path: str) -> Iterator[str]:
    """Yield lines from the log file one at a time."""
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            yield line.rstrip("\n")
