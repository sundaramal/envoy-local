"""CLI commands for managing TLS certificates in envoy-local."""

import sys
from envoy_local import cert as certmod


def cmd_cert_generate(args) -> None:
    """Generate a self-signed certificate for a given name."""
    name = args.name
    days = getattr(args, "days", 365)
    cert_dir = getattr(args, "cert_dir", certmod.DEFAULT_CERT_DIR)

    if certmod.cert_exists(name, cert_dir=cert_dir):
        print(f"Certificate '{name}' already exists. Use --force to overwrite.", file=sys.stderr)
        if not getattr(args, "force", False):
            sys.exit(1)
        certmod.delete_cert(name, cert_dir=cert_dir)

    try:
        info = certmod.generate_self_signed(name, cert_dir=cert_dir, days=days)
        print(f"Generated certificate '{name}'")
        print(f"  cert: {info.cert_path}")
        print(f"  key:  {info.key_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"Error generating certificate: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_cert_list(args) -> None:
    """List all stored certificates."""
    cert_dir = getattr(args, "cert_dir", certmod.DEFAULT_CERT_DIR)
    names = certmod.list_certs(cert_dir=cert_dir)
    if not names:
        print("No certificates found.")
        return
    for name in names:
        print(name)


def cmd_cert_delete(args) -> None:
    """Delete a named certificate."""
    name = args.name
    cert_dir = getattr(args, "cert_dir", certmod.DEFAULT_CERT_DIR)

    if not certmod.cert_exists(name, cert_dir=cert_dir):
        print(f"Certificate '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    certmod.delete_cert(name, cert_dir=cert_dir)
    print(f"Deleted certificate '{name}'.")


def cmd_cert_info(args) -> None:
    """Show paths for a named certificate."""
    name = args.name
    cert_dir = getattr(args, "cert_dir", certmod.DEFAULT_CERT_DIR)

    try:
        info = certmod.get_cert_info(name, cert_dir=cert_dir)
        print(f"Certificate '{name}'")
        print(f"  cert: {info.cert_path}")
        print(f"  key:  {info.key_path}")
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
