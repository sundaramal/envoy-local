"""Generate summary reports from parsed Envoy access logs."""

from __future__ import annotations

from typing import List, Dict, Any

from envoy_local.log_parser import (
    parse_access_log_file,
    filter_by_status,
    summarize_by_status,
    average_duration,
)


def generate_report(log_path: str) -> Dict[str, Any]:
    """Parse a log file and return a structured summary report."""
    entries = parse_access_log_file(log_path)

    if not entries:
        return {
            "total_requests": 0,
            "status_summary": {},
            "average_duration_ms": None,
            "error_rate": 0.0,
            "top_paths": [],
        }

    status_summary = summarize_by_status(entries)
    avg_dur = average_duration(entries)

    error_entries = filter_by_status(entries, 500, 599)
    error_rate = len(error_entries) / len(entries) if entries else 0.0

    path_counts: Dict[str, int] = {}
    for entry in entries:
        path = entry.get("path", "unknown")
        path_counts[path] = path_counts.get(path, 0) + 1

    top_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_requests": len(entries),
        "status_summary": status_summary,
        "average_duration_ms": avg_dur,
        "error_rate": round(error_rate, 4),
        "top_paths": [{"path": p, "count": c} for p, c in top_paths],
    }


def format_report(report: Dict[str, Any]) -> str:
    """Format a report dict into a human-readable string."""
    lines: List[str] = []
    lines.append(f"Total Requests : {report['total_requests']}")
    lines.append(f"Avg Duration   : {report['average_duration_ms']} ms")
    lines.append(f"Error Rate     : {report['error_rate'] * 100:.2f}%")

    lines.append("Status Summary:")
    for status, count in sorted(report["status_summary"].items()):
        lines.append(f"  {status}: {count}")

    lines.append("Top Paths:")
    for entry in report["top_paths"]:
        lines.append(f"  {entry['path']}: {entry['count']} requests")

    return "\n".join(lines)


def print_report(log_path: str) -> None:
    """Convenience function to print a formatted report to stdout."""
    report = generate_report(log_path)
    print(format_report(report))
