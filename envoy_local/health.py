"""Health check utilities for local Envoy proxy instances."""

import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


@dataclass
class HealthStatus:
    alive: bool
    admin_reachable: bool
    ready: bool
    message: str


def check_admin_endpoint(admin_port: int, timeout: float = 2.0) -> bool:
    """Return True if the Envoy admin endpoint responds."""
    url = f"http://127.0.0.1:{admin_port}/ready"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def wait_for_admin(
    admin_port: int,
    retries: int = 10,
    interval: float = 0.5,
) -> bool:
    """Poll the admin endpoint until it responds or retries are exhausted."""
    for _ in range(retries):
        if check_admin_endpoint(admin_port):
            return True
        time.sleep(interval)
    return False


def get_health_status(
    admin_port: int,
    pid: Optional[int],
    is_alive_fn=None,
) -> HealthStatus:
    """Aggregate health information for a running Envoy process."""
    from envoy_local.process import is_process_alive

    check_alive = is_alive_fn or is_process_alive

    if pid is None:
        return HealthStatus(
            alive=False,
            admin_reachable=False,
            ready=False,
            message="No PID found — Envoy is not running.",
        )

    alive = check_alive(pid)
    if not alive:
        return HealthStatus(
            alive=False,
            admin_reachable=False,
            ready=False,
            message=f"Process {pid} is not alive.",
        )

    admin_ok = check_admin_endpoint(admin_port)
    return HealthStatus(
        alive=True,
        admin_reachable=admin_ok,
        ready=admin_ok,
        message="Envoy is running and ready." if admin_ok else "Envoy process alive but admin not reachable.",
    )
