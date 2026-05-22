"""Structured parsing helpers for Envoy access log lines."""

import re
from typing import Dict, List, Optional

# Matches a common Envoy text access-log format:
# [2024-01-01T00:00:00.000Z] "GET /path HTTP/1.1" 200 - 0 512 5 4 "-" "curl" "-" "-"
ACCESS_LOG_RE = re.compile(
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>[^"]+)"\s+'
    r'(?P<status>\d+)\s+\S+\s+\d+\s+(?P<bytes_out>\d+)\s+'
    r'(?P<duration>\d+)'
)


def parse_access_log_line(line: str) -> Optional[Dict[str, str]]:
    """Parse a single Envoy access log line into a dict, or None if unmatched."""
    m = ACCESS_LOG_RE.search(line)
    if not m:
        return None
    return {
        "timestamp": m.group("timestamp"),
        "method": m.group("method"),
        "path": m.group("path"),
        "protocol": m.group("protocol").strip(),
        "status": m.group("status"),
        "bytes_out": m.group("bytes_out"),
        "duration_ms": m.group("duration"),
    }


def parse_access_log_file(log_path: str) -> List[Dict[str, str]]:
    """Parse all access log lines from *log_path*, skipping unparseable lines."""
    results: List[Dict[str, str]] = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parsed = parse_access_log_line(line)
            if parsed:
                results.append(parsed)
    return results


def filter_by_status(entries: List[Dict[str, str]], status_prefix: str) -> List[Dict[str, str]]:
    """Return entries whose HTTP status starts with *status_prefix* (e.g. '5' for 5xx)."""
    return [e for e in entries if e["status"].startswith(status_prefix)]


def summarize_by_status(entries: List[Dict[str, str]]) -> Dict[str, int]:
    """Return a count of log entries grouped by HTTP status code."""
    summary: Dict[str, int] = {}
    for entry in entries:
        code = entry["status"]
        summary[code] = summary.get(code, 0) + 1
    return summary


def average_duration(entries: List[Dict[str, str]]) -> Optional[float]:
    """Return the mean request duration in ms, or None if *entries* is empty."""
    if not entries:
        return None
    total = sum(int(e["duration_ms"]) for e in entries)
    return total / len(entries)
