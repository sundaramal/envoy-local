"""Snapshot management for saving and restoring Envoy configurations."""

import json
import os
from datetime import datetime
from typing import List, Optional

DEFAULT_SNAPSHOT_DIR = os.path.expanduser("~/.envoy-local/snapshots")


def _ensure_snapshot_dir(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)


def save_snapshot(
    config_dict: dict,
    name: Optional[str] = None,
    directory: str = DEFAULT_SNAPSHOT_DIR,
) -> str:
    """Serialize config_dict to a JSON snapshot file. Returns the file path."""
    _ensure_snapshot_dir(directory)
    if name is None:
        name = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{name}.json"
    path = os.path.join(directory, filename)
    with open(path, "w") as fh:
        json.dump(config_dict, fh, indent=2)
    return path


def load_snapshot(
    name: str,
    directory: str = DEFAULT_SNAPSHOT_DIR,
) -> dict:
    """Load a previously saved snapshot by name. Raises FileNotFoundError if missing."""
    path = os.path.join(directory, f"{name}.json")
    with open(path, "r") as fh:
        return json.load(fh)


def list_snapshots(directory: str = DEFAULT_SNAPSHOT_DIR) -> List[str]:
    """Return snapshot names (without extension) sorted by modification time desc."""
    if not os.path.isdir(directory):
        return []
    entries = [
        f for f in os.listdir(directory) if f.endswith(".json")
    ]
    entries.sort(
        key=lambda f: os.path.getmtime(os.path.join(directory, f)),
        reverse=True,
    )
    return [os.path.splitext(f)[0] for f in entries]


def delete_snapshot(
    name: str,
    directory: str = DEFAULT_SNAPSHOT_DIR,
) -> bool:
    """Delete a snapshot by name. Returns True if deleted, False if not found."""
    path = os.path.join(directory, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
