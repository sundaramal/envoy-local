"""Utilities for detecting and interacting with existing Envoy processes."""

import os
import signal
from pathlib import Path
from typing import Optional

PID_FILE = Path(".envoy_local.pid")


def read_pid() -> Optional[int]:
    """Read the PID from the PID file, returning None if not found."""
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def is_process_alive(pid: int) -> bool:
    """Check if a process with the given PID is alive."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def kill_process(pid: int, timeout: int = 5) -> bool:
    """Send SIGTERM to a process, falling back to SIGKILL. Returns True on success."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return False

    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not is_process_alive(pid):
            return True
        time.sleep(0.2)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return not is_process_alive(pid)


def get_running_pid() -> Optional[int]:
    """Return the PID of a running Envoy process managed by envoy-local, or None."""
    pid = read_pid()
    if pid is not None and is_process_alive(pid):
        return pid
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)
    return None
