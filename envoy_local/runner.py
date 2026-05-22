"""Runner module for starting and stopping local Envoy proxy processes."""

import os
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from envoy_local.config import EnvoyConfig

DEFAULT_ENVOY_BINARY = os.environ.get("ENVOY_BINARY", "envoy")
PID_FILE = Path(".envoy_local.pid")


class EnvoyRunner:
    """Manages a local Envoy proxy process lifecycle."""

    def __init__(self, config: EnvoyConfig, envoy_binary: str = DEFAULT_ENVOY_BINARY):
        self.config = config
        self.envoy_binary = envoy_binary
        self._process: Optional[subprocess.Popen] = None
        self._config_file: Optional[tempfile.NamedTemporaryFile] = None

    def _write_config(self) -> str:
        """Write Envoy config to a temporary file and return its path."""
        self._config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, prefix="envoy_local_"
        )
        yaml.dump(self.config.to_envoy_yaml(), self._config_file)
        self._config_file.flush()
        return self._config_file.name

    def start(self) -> int:
        """Start the Envoy process. Returns the PID."""
        if self.is_running():
            raise RuntimeError(f"Envoy is already running with PID {self.pid}")

        config_path = self._write_config()
        cmd = [self.envoy_binary, "-c", config_path]

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        PID_FILE.write_text(str(self._process.pid))
        return self._process.pid

    def stop(self) -> None:
        """Stop the running Envoy process."""
        if not self.is_running():
            raise RuntimeError("No Envoy process is currently running.")

        self._process.send_signal(signal.SIGTERM)
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
        finally:
            self._cleanup()

    def is_running(self) -> bool:
        """Check if an Envoy process is currently running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def pid(self) -> Optional[int]:
        """Return the PID of the running process, or None."""
        if self._process:
            return self._process.pid
        return None

    def _cleanup(self) -> None:
        """Remove temporary files and PID file."""
        if self._config_file:
            try:
                os.unlink(self._config_file.name)
            except FileNotFoundError:
                pass
        if PID_FILE.exists():
            PID_FILE.unlink()
        self._process = None
