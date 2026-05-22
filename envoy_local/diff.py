"""Utilities for diffing two Envoy configurations."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[Tuple[str, Any, Any]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Recursively flatten a nested dict/list into dot-separated keys."""
    items: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            items.update(_flatten(v, full_key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            full_key = f"{prefix}[{i}]"
            items.update(_flatten(v, full_key))
    else:
        items[prefix] = obj
    return items


def diff_configs(old: Dict[str, Any], new: Dict[str, Any]) -> DiffResult:
    """Compare two config dicts and return a DiffResult."""
    result = DiffResult()
    old_flat = _flatten(old)
    new_flat = _flatten(new)

    old_keys = set(old_flat.keys())
    new_keys = set(new_flat.keys())

    for key in sorted(new_keys - old_keys):
        result.added.append(key)

    for key in sorted(old_keys - new_keys):
        result.removed.append(key)

    for key in sorted(old_keys & new_keys):
        if old_flat[key] != new_flat[key]:
            result.changed.append((key, old_flat[key], new_flat[key]))

    return result


def format_diff(result: DiffResult) -> str:
    """Format a DiffResult as a human-readable string."""
    if not result.has_changes:
        return "No differences found."

    lines = []
    for key in result.added:
        lines.append(f"+ {key}")
    for key in result.removed:
        lines.append(f"- {key}")
    for key, old_val, new_val in result.changed:
        lines.append(f"~ {key}: {json.dumps(old_val)} -> {json.dumps(new_val)}")
    return "\n".join(lines)
