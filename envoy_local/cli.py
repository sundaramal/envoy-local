"""CLI entry points for envoy-local."""

import sys
from envoy_local.runner import EnvoyRunner
from envoy_local.process import get_running_pid
from envoy_local.health import get_health_status, wait_for_admin
from envoy_local.stats import get_stats, filter_stats


def cmd_start(config, binary: str = "envoy") -> None:
    runner = EnvoyRunner(config, binary=binary)
    try:
        runner.start()
        print(f"Envoy started (PID {get_running_pid(config.pid_file)}).")
        if wait_for_admin(config.admin_port, retries=12, interval=0.5):
            print(f"Admin interface ready at http://127.0.0.1:{config.admin_port}")
        else:
            print("Warning: admin interface did not become ready in time.", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Envoy binary not found at '{binary}'.", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_stop(config) -> None:
    runner = EnvoyRunner(config)
    try:
        runner.stop()
        print("Envoy stopped.")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_status(config) -> None:
    pid = get_running_pid(config.pid_file)
    status = get_health_status(config.admin_port, pid)
    print(f"Alive        : {status.alive}")
    print(f"Admin ready  : {status.admin_reachable}")
    print(f"Message      : {status.message}")


def cmd_stats(config, prefix: str = "") -> None:
    """Print Envoy stats, optionally filtered by a key prefix."""
    raw = get_stats(config.admin_port)
    if raw is None:
        print("Error: could not reach Envoy admin endpoint.", file=sys.stderr)
        sys.exit(1)
    stats = filter_stats(raw, prefix) if prefix else raw
    if not stats:
        print(f"No stats found for prefix '{prefix}'.")
        return
    for key, value in sorted(stats.items()):
        print(f"{key}: {value}")
