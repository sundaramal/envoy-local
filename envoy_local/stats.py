"""Fetch and parse Envoy statistics from the admin endpoint."""

import urllib.request
import urllib.error
from typing import Dict, Optional


def fetch_stats_text(admin_port: int, timeout: float = 3.0) -> Optional[str]:
    """Retrieve raw stats from /stats on the Envoy admin interface."""
    url = f"http://127.0.0.1:{admin_port}/stats"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, OSError):
        return None


def parse_stats(raw: str) -> Dict[str, str]:
    """Parse Envoy stats text format into a key/value dictionary."""
    result: Dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or ": " not in line:
            continue
        key, _, value = line.partition(": ")
        result[key.strip()] = value.strip()
    return result


def get_stats(admin_port: int) -> Optional[Dict[str, str]]:
    """Return parsed stats dict, or None if the admin endpoint is unreachable."""
    raw = fetch_stats_text(admin_port)
    if raw is None:
        return None
    return parse_stats(raw)


def filter_stats(stats: Dict[str, str], prefix: str) -> Dict[str, str]:
    """Return only stats whose keys start with *prefix*."""
    return {k: v for k, v in stats.items() if k.startswith(prefix)}
