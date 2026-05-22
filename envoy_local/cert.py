"""TLS certificate utilities for local Envoy configurations."""

import os
import subprocess
import datetime
from dataclasses import dataclass
from typing import Optional

DEFAULT_CERT_DIR = os.path.expanduser("~/.envoy-local/certs")


@dataclass
class CertInfo:
    cert_path: str
    key_path: str
    expires_at: Optional[datetime.datetime] = None
    subject: Optional[str] = None


def _ensure_cert_dir(cert_dir: str = DEFAULT_CERT_DIR) -> str:
    os.makedirs(cert_dir, exist_ok=True)
    return cert_dir


def generate_self_signed(name: str, cert_dir: str = DEFAULT_CERT_DIR, days: int = 365) -> CertInfo:
    """Generate a self-signed certificate and key pair."""
    _ensure_cert_dir(cert_dir)
    cert_path = os.path.join(cert_dir, f"{name}.crt")
    key_path = os.path.join(cert_dir, f"{name}.key")

    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_path,
            "-out", cert_path,
            "-days", str(days),
            "-nodes",
            "-subj", f"/CN={name}/O=envoy-local",
        ],
        check=True,
        capture_output=True,
    )
    return CertInfo(cert_path=cert_path, key_path=key_path)


def cert_exists(name: str, cert_dir: str = DEFAULT_CERT_DIR) -> bool:
    """Check whether a named cert/key pair already exists."""
    cert_path = os.path.join(cert_dir, f"{name}.crt")
    key_path = os.path.join(cert_dir, f"{name}.key")
    return os.path.isfile(cert_path) and os.path.isfile(key_path)


def get_cert_info(name: str, cert_dir: str = DEFAULT_CERT_DIR) -> CertInfo:
    """Return paths for an existing named certificate pair."""
    cert_path = os.path.join(cert_dir, f"{name}.crt")
    key_path = os.path.join(cert_dir, f"{name}.key")
    if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
        raise FileNotFoundError(f"Certificate '{name}' not found in {cert_dir}")
    return CertInfo(cert_path=cert_path, key_path=key_path)


def delete_cert(name: str, cert_dir: str = DEFAULT_CERT_DIR) -> None:
    """Remove a named certificate pair from disk."""
    for ext in (".crt", ".key"):
        path = os.path.join(cert_dir, f"{name}{ext}")
        if os.path.isfile(path):
            os.remove(path)


def list_certs(cert_dir: str = DEFAULT_CERT_DIR) -> list:
    """Return names of all certificates stored in cert_dir."""
    if not os.path.isdir(cert_dir):
        return []
    names = set()
    for fname in os.listdir(cert_dir):
        if fname.endswith(".crt"):
            names.add(fname[:-4])
    return sorted(names)
