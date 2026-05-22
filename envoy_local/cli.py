"""CLI entry points for envoy-local start/stop/status commands."""

import sys

from envoy_local.config import EnvoyConfig
from envoy_local.process import get_running_pid, kill_process, PID_FILE
from envoy_local.runner import EnvoyRunner


def cmd_start(config: EnvoyConfig, envoy_binary: str = "envoy") -> int:
    """Start a local Envoy instance. Returns exit code."""
    existing = get_running_pid()
    if existing:
        print(f"[envoy-local] Envoy is already running (PID {existing}).", file=sys.stderr)
        return 1

    runner = EnvoyRunner(config, envoy_binary=envoy_binary)
    try:
        pid = runner.start()
        print(f"[envoy-local] Envoy started with PID {pid}.")
        return 0
    except FileNotFoundError:
        print(
            f"[envoy-local] Envoy binary '{envoy_binary}' not found. "
            "Set ENVOY_BINARY or ensure envoy is on PATH.",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"[envoy-local] Failed to start Envoy: {exc}", file=sys.stderr)
        return 3


def cmd_stop() -> int:
    """Stop the running Envoy instance. Returns exit code."""
    pid = get_running_pid()
    if pid is None:
        print("[envoy-local] No running Envoy process found.", file=sys.stderr)
        return 1

    success = kill_process(pid)
    if success:
        PID_FILE.unlink(missing_ok=True)
        print(f"[envoy-local] Envoy (PID {pid}) stopped.")
        return 0
    else:
        print(f"[envoy-local] Failed to stop Envoy (PID {pid}).", file=sys.stderr)
        return 1


def cmd_status() -> int:
    """Print the status of the Envoy process. Returns exit code."""
    pid = get_running_pid()
    if pid:
        print(f"[envoy-local] Envoy is running (PID {pid}).")
        return 0
    else:
        print("[envoy-local] Envoy is not running.")
        return 1
