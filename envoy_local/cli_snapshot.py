"""CLI commands for snapshot management (save / load / list / delete)."""

import sys
from typing import Optional

from envoy_local.config import EnvoyConfig
from envoy_local.snapshot import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
)


def cmd_snapshot_save(config: EnvoyConfig, name: Optional[str] = None) -> None:
    """Serialize *config* to a snapshot file and print the saved path."""
    data = config.to_dict()
    path = save_snapshot(data, name=name)
    print(f"Snapshot saved: {path}")


def cmd_snapshot_load(name: str) -> Optional[EnvoyConfig]:
    """Load a snapshot by *name* and return a reconstructed EnvoyConfig."""
    try:
        data = load_snapshot(name)
    except FileNotFoundError:
        print(f"Error: snapshot '{name}' not found.", file=sys.stderr)
        return None
    config = EnvoyConfig.from_dict(data)
    print(f"Snapshot '{name}' loaded successfully.")
    return config


def cmd_snapshot_list() -> None:
    """Print all available snapshot names, newest first."""
    names = list_snapshots()
    if not names:
        print("No snapshots found.")
        return
    print(f"{'NAME':<30}")
    print("-" * 30)
    for name in names:
        print(name)


def cmd_snapshot_delete(name: str) -> None:
    """Delete a snapshot by *name*."""
    removed = delete_snapshot(name)
    if removed:
        print(f"Snapshot '{name}' deleted.")
    else:
        print(f"Error: snapshot '{name}' not found.", file=sys.stderr)
        sys.exit(1)
